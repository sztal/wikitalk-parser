"""Wikipedia talk threads parser."""
import re
import html
from typing import Iterable, Union, Optional, Tuple
from .base import WikiParser, WikiParserRX


class WikiParserThreadsRX(WikiParserRX):
    """Container-class with pre-compiled regex objects."""
    thread = re.compile(r"(^\s*)(?==)", re.IGNORECASE | re.MULTILINE)
    title = re.compile(r"=+(?P<title>.*?)=+", re.IGNORECASE)
    signature = re.compile(
        r"(\[\[|\{\{)User([ _]talk)?:.*?(\]\]|\}\}).*?\([A-Z]{3,3}\)",
        re.IGNORECASE
    )
    user = re.compile(
        r"(\[\[|\{\{)User([ _]talk)?:"
        r"(?P<user>[^\|#/\[\]\{\}]*)",
        re.IGNORECASE
    )
    timestamp = re.compile(
        r"(?P<ts>(?<=\s)[\w\d:\.,-/\s]*?)"
        r"[\s\W]*\(UTC\)\s*$",
        re.IGNORECASE
    )
    depth = re.compile(r"^\s*[:\*#]+")
    outdent = re.compile(
        r"^\s*[:\*#]*\{\{(outdent|od)\d?(\|(\d+|:+))?\}\}"
    )
    nl = re.compile(r"(\n|$)",)
    # Sanitize content
    c_indents = re.compile(r"^\s*[:*#]+")
    c_wiki_multiline = re.compile(r"\{\|.*?\|\}")
    c_html_comments = re.compile(r"<!--.*?-->")
    c_qmark_single = re.compile(r"'+")
    c_qmark_double = re.compile(r"\"+")
    c_signature1 = re.compile(
        r"[\(\[\{]*User[\s_]*(talk)?:[^\[\{\(]*?\([A-Z]{3}\)",
        re.IGNORECASE
    )
    c_signature2 = re.compile(
        r"[\(\[\{]+User[\s_]*(talk)?:[^\[\{\(]*?[\]\}\)]+\s*$",
        re.IGNORECASE
    )
    c_links_label = re.compile(r"\[\[.*?([^\|:]*?)\]\]")
    c_html_tags = re.compile(r"</?.*?>")
    c_html_wiki_templates = re.compile(r"\{\{.*?\}\}")
    c_whitespace_long = re.compile(r"\n+|\t+|\s{4,}")
    c_whitespace_short = re.compile(r"\s{1,3}")
    c_html_entities = re.compile(r"&[a-z]+;")


class WikiParserThreads(WikiParser):
    """Parser for threads on Wikipedia talk pages.

    The parser is based on some assumptions about the structure of talk
    pages which are usually correct, but in some cases may lead to
    somewhat distorted results (e.g. multiple posts lumped into one).

    The main assumption is that posts of individual
    users are signed properly so they end with a signature including
    userpage link and a (UTC) timestamp. In our experience
    most of discussions (at least on English Wikipedia) consist almost exclusively
    of messages with proper signatures. However, some posts may not have correct
    signatures  and in such a case they may not be extracted at all or unsigned
    posts may be lumped together with previous properly signed posts.

    The second main assumption is that different discussion threads on a single
    talk page are separated by section headers starting  which can be detected
    with ``^\\s*==+\\s*`` regex. Again, this a very common convention on Wikipedia
    but in some rare cases it may not be followed leading to incorrect results.

    Attributes
    ----------
    source : str
        Source (Wiki markup) of a page.
    rx : type
        Container-class with pre-compiled regex objects.
    """
    # Class attributes
    rx = WikiParserThreadsRX

    # -------------------------------------------------------------------------

    def parse(self, sanitize_content: bool = True) -> Iterable[dict]:
        """Parse posts in threads.

        Parameters
        ----------
        sanitize_content
            Should additional field with sanitized content be created.
            Sanitized content has most of Wiki and HTML markup removed
            (and HTML entities are decoded).

        Yields
        ------
        post
            Posts represented as dictionaries.
            Comment tree hierarchy is retained in `parent_idx`
            and individual threads are identified by `thread_idx` field.
        """
        for thread in self._parse_threads():
            dtree = thread.pop('dtree')
            for post in self._unwind(dtree, idx=0, **thread):
                if sanitize_content:
                    post['content_sanitized'] = \
                        self._sanitize_content(post['content'])
                yield post

    def _sanitize_content(self, s: str) -> str:
        s = self.rx.c_indents.sub(r"", s)
        s = self.rx.c_wiki_multiline.sub(r"", s)
        s = self.rx.c_html_comments.sub(r"", s)
        s = self.rx.c_qmark_single.sub(r"'", s)
        s = self.rx.c_qmark_double.sub(r'"', s)
        s = self.rx.c_signature1.sub(r"", s)
        s = self.rx.c_signature2.sub(r"", s)
        s = self.rx.c_links_label.sub(r"\1", s)
        s = self.rx.c_html_tags.sub(r"", s)
        s = self.rx.c_html_wiki_templates.sub(r"", s)
        s = self.rx.c_whitespace_long.sub(r"    ", s)
        s = self.rx.c_whitespace_short.sub(r" ", s)
        if self.rx.c_html_entities.search(s):
            s = html.unescape(s)
        return s.strip()

    def _unwind(
        self,
        post: dict,
        idx: Union[str, int],
        parent: Optional[Union[str, int]] = None,
        **kwds
    ) -> Iterable[dict]:
        """Unwind post and subposts."""
        idx = str(idx)
        comments = post.pop('comments', [])
        yield { **kwds, 'post_idx': idx, 'parent_idx': parent, **post }
        for i, comment in enumerate(comments, 1):
            yield from self._unwind(comment, idx=f"{idx}.{i}", parent=idx, **kwds)

    def _parse_threads(self) -> Iterable[dict]:
        """Parse threads and posts."""
        tid = 0
        for thread in self._iter_threads():
            title, thread = thread
            thread = {
                'topic': title,
                'posts': [
                    self._process_post(sig, post)
                    for sig, post in self._iter_posts(thread)
                ]
            }
            if thread['posts']:
                tid += 1
                thread['thread_idx'] = tid
                yield self._process_thread(thread)

    def _iter_threads(self) -> Iterable[Tuple[str, str]]:
        """Iterate over threads.

        Threads are separated by header starting with `==`.
        """
        for thread in self.rx.thread.split(self.source):
            thread = thread.strip()
            if thread:
                title = self.rx.title.match(thread)
                if title:
                    thread = thread[title.end():]
                    title = title.group('title').strip()
                if thread:
                    thread = thread.strip()
                    yield title, thread

    def _iter_posts(self, thread: str) -> Iterable[Tuple[str, str]]:
        """Iterate over posts in a thread."""
        # This is uglt
        sigs = list(self.rx.signature.finditer(thread))
        N = len(sigs)
        start = None
        for idx, match in enumerate(sigs, 1):
            if idx < N:
                end = self.rx.nl.search(thread, match.end()).start()
            else:
                end = None
            post = thread[slice(start, end)]
            yield match.group(), post
            start = end

    def _process_post(self, sig: str, post: str) -> dict:
        """Process signatures and posts in a tidy dictionary."""
        user_name = None
        for match in self.rx.user.finditer(sig):
            user_name = match.group('user')
        timestamp = self.rx.timestamp.search(sig)
        if timestamp:
            timestamp = timestamp.group('ts')
        content = post.strip()
        depth, outdent = self._count_depth(content)
        dct = {
            'user_name': self.sanitize_user_name(user_name),
            'timestamp': self.parse_date(timestamp),
            'depth': depth,
            'dots': depth,
            'outdent': outdent,
            'content': content,
            'comments': []
        }
        return dct

    def _process_thread(self, thread: str) -> str:
        posts = thread.pop('posts', [])
        dtree, posts = posts[0], posts[1:]
        dtree['depth'] = dtree['dots'] = 0
        stack = [ dtree ]
        for post in posts:
            post['dots'] += 1
            parent = None
            while parent is None:
                parent = stack[-1]
                if post['outdent']:
                    post['depth'] = parent['depth'] + 1
                elif post['dots'] <= parent['dots']:
                    stack.pop()
                    parent = None
            post['depth'] = parent['depth'] + 1
            parent['comments'].append(post)
            stack.append(post)
        thread = { **thread, 'dtree': dtree }
        self._clean_thread(thread)
        return thread

    def _clean_thread(self, thread: str) -> None:
        def _clean(dtree):
            del dtree['dots']
            del dtree['outdent']
            for dt in dtree['comments']:
                _clean(dt)
        _clean(thread['dtree'])

    def _count_depth(self, s: str) -> Tuple[int, str]:
        m = self.rx.depth.match(s)
        depth = len(m.group()) if m else 0
        outdent = self.rx.outdent.match(s)
        return depth, outdent
