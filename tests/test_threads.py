"""Test threads parser."""
from ipaddress import ip_address
import pytest
from wikitalk_parser import WikiParserThreads


class TestThreadsParser:

    def test_parse(self, talkpage):
        source, parsed, sanitize_content = talkpage
        threads = WikiParserThreads(source)
        threads = list(threads.parse(sanitize_content=sanitize_content))
        assert threads == parsed
