import importlib.util
from pathlib import Path


def load_generate_feed_module():
    path = Path(__file__).parent.parent / 'deployment' / 'generate_feed.py'
    spec = importlib.util.spec_from_file_location('generate_feed', path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_extract_title_basic():
    module = load_generate_feed_module()
    content = '<html><head><title>My Basic Title</title></head><body></body></html>'
    assert module._extract_title(content, 'stem_name') == 'My Basic Title'


def test_extract_title_with_attributes():
    module = load_generate_feed_module()
    content = '<html><head><title class="some-class" id="title-id">Title with attributes</title></head><body></body></html>'
    assert module._extract_title(content, 'stem_name') == 'Title with attributes'


def test_extract_title_multiline():
    module = load_generate_feed_module()
    content = '''<html>
<head>
  <title>
    Multi-line Title
  </title>
</head>
<body></body></html>'''
    assert module._extract_title(content, 'stem_name') == 'Multi-line Title'


def test_extract_title_missing_uses_fallback():
    module = load_generate_feed_module()
    content = '<html><head></head><body>No title here</body></html>'
    assert module._extract_title(content, 'my_test_stem') == 'My Test Stem'


def test_extract_title_html_entities_unescaped():
    module = load_generate_feed_module()
    content = '<html><head><title>Title &amp; with &lt;tags&gt; &amp; &#39;quotes&#39;</title></head><body></body></html>'
    assert module._extract_title(content, 'stem_name') == "Title & with <tags> & 'quotes'"
