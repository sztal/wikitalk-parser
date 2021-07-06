"""*PyTest* configuration and general purpose fixtures."""
from pathlib import Path
from datetime import datetime
from itertools import product
import json
import pytest


_datapath = (Path(__file__).parent.parent/'examples'/'data').absolute()
_testcases = list(_datapath.glob('*.json'))
_talkpage_params = list(product(_testcases, [True, False]))

@pytest.fixture(scope='session', params=_talkpage_params)
def talkpage(request):
    """Monty Python talk page markup and parsed threads."""
    path, sanitize_content = request.param
    with open(path, 'r') as fh:
        data = json.load(fh)
    source, parsed = data['source'], data['threads']
    for d in parsed:
        d['timestamp'] = datetime.strptime(d['timestamp'], "%Y-%m-%d %H:%M:%S")
        if not sanitize_content:
            del d['content_sanitized']
    return source, parsed, sanitize_content
