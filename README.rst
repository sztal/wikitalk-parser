=============================
Wikitalk parser
=============================

.. image:: https://travis-ci.com/sztal/wikitalk-parser.png?branch=master
    :target: https://travis-ci.com/sztal/wikitalk-parser

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.4743619.svg
   :target: https://doi.org/10.5281/zenodo.4743619


Wikipedia talk threads parser aware of outdent formatting.
It is a simple yet relatively efficient pure Python implementation
based on pattern matching with regular expressions. It can be used to
extract talk page discussions from hundreds of thousands of pages in
a reasonably short time.

The parser is based on some assumptions about the structure of talk
pages which are usually correct, but in some cases may lead to
somewhat distorted results (e.g. multiple posts lumped into one).

The main assumption is that posts of individual
users are signed properly so they end with a signature including
userpage link and a (UTC) timestamp. In our experience
most of discussions (at least on English Wikipedia) consist almost exclusively
of messages with proper signatures. However, some posts may not have correct
signatures  and in such a case they may not be extracted at all or (more likely)
unsigned posts may be lumped together with subsequent properly signed posts.

The second main assumption is that different discussion threads on a single
talk page are separated by section headers starting  which can be detected
with `^\s*==+\s*` regex. Again, this a very common convention on Wikipedia
but in some rare cases it may not be followed leading to incorrect results.


Dependencies
-------------

* `Python3.7+`. It may work for earlier versions of Python3 but it is not tested.
  It also should work with PyPy, but again, this is not guaranteed.
* `python-dateutil>=2.8`. This is only external dependency.

Installation
------------

This package can be installed directly from its Github repository
but not yet from PyPI (we do not consider it mature enough to justify
polluting PyPI namespace). However, when installing from Github it may be
necessary to install `python-dateutil` by hand.

.. code-block:: bash

    # INSTALL DEPENDENCIES
    pip install 'python-dateutil>=2.8'

    # OVER SSH (RECOMMENDED)
    pip install git+ssh://git@github.com/sztal/wikitalk-parser.git
    # OVER HTTPS (DEPRECATED)
    pip install git+https://github.com/sztal/wikitalk-parser.git


Usage example
-------------

Here we download `talk page <https://en.wikipedia.org/wiki/Talk:Monty_Python>`_
of Monty Python page on English Wikipedia using Wikipedia API Cirrus Doc
endpoint and use the parser to extract all discussion threads.

.. code-block:: python

    resp = requests.get('https://en.wikipedia.org/w/api.php', params=dict(
        action='query',
        format='json',
        prop='cirrusdoc',
        titles='Talk:Monty_Python'
    ))
    data = resp.json()
    source = data['query']['pages']['18949']['cirrusdoc'][0]['source']['source_text']

Using the parser is very easy. First an instance needs to be initialized on
a string with Wiki markup of a page. And then `.parse()` method can be called
which returns a generator of subsequent posts. Hierarchy of threads and
posts within threads is retained by a set of additional index fields.

Each post is a simple `dict` object with the following fields:

`topic`
    thread title/topic
`thread_idx`
    thread index according to the actual order on page
    and counting from `1`.
`post_idx`
    index of a post within a thread according to the order of appearance.
`parent_idx`
    index of the parent post.
`user_name`
    user name of the author.
`timestamp`
    post creation timestamp as `datetime` object.
`depth`
    depth within the discussion tree.
`content`
    raw content of the post as extrected from Wiki markup.
`content_sanitized`
    content cleaned from most of Wiki and HTML markup.

Note that thanks to the fact that the data is returned as a simple flat
list of homogeneous `dict` objects output of the parser can be easily fit
into different convenient data structures such as
`Pandas <https://pandas.pydata.org/>`_ data frames.

.. code-block:: python

    threads = WikiParserThreads(source)
    list(threads.parse()

However, in general posts are returned through a generator so only data
for a single discussion thread (whole thread not a single post) needs
to be stored in working memory at any single point in time.

.. code-block:: python

    threads = WikiParserThreads(source).parse()
    next(threads)


Bugs & other issues
-------------------

This is a very simple software and comes with no guarantees whatsover
(see the licence). However, if you find any bugs or other problems you are
welcome to notify us by setting up a
`Github issue <https://github.com/sztal/wikitalk-parser/issues>`_.


Contact
-------

Szymon Talaga `<stalaga@protonmail.com>`
