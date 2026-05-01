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

def test_extract_description_meta_tag():
    module = load_generate_feed_module()

    # Standard format
    content = '<html><head><meta name="description" content="A test description"></head><body></body></html>'
    assert module._extract_description(content, 'test.html', {}) == 'A test description'

    # Different quotes
    content2 = "<html><head><meta name='description' content='Another description'></head><body></body></html>"
    assert module._extract_description(content2, 'test.html', {}) == 'Another description'

    # Case insensitivity
    content3 = '<HTML><HEAD><META NAME="DESCRIPTION" CONTENT="Case insensitive"></HEAD><BODY></BODY></HTML>'
    assert module._extract_description(content3, 'test.html', {}) == 'Case insensitive'

def test_extract_description_subtitle():
    module = load_generate_feed_module()

    # Simple subtitle
    content = '<html><body><h2 class="subtitle">A simple subtitle</h2></body></html>'
    assert module._extract_description(content, 'test.html', {}) == 'A simple subtitle'

    # Subtitle with internal tags
    content2 = '<html><body><p class="custom-subtitle">Subtitle with bold text</p></body></html>'
    assert module._extract_description(content2, 'test.html', {}) == 'Subtitle with bold text'

    # Subtitle with extra spacing and entities
    content3 = '<html><body><div class="subtitle">\n  Spaced   out &amp; entity \n</div></body></html>'
    assert module._extract_description(content3, 'test.html', {}) == 'Spaced out & entity'

    # Subtitle exceeding 120 characters
    long_text = 'A' * 125
    content4 = f'<html><body><h3 class="subtitle">{long_text}</h3></body></html>'
    expected_long = 'A' * 120 + '…'
    assert module._extract_description(content4, 'test.html', {}) == expected_long

def test_extract_description_fallback_dict():
    module = load_generate_feed_module()

    content = '<html><body><p>No description or subtitle here</p></body></html>'
    descriptions = {'test.html': 'Description from dict'}

    assert module._extract_description(content, 'test.html', descriptions) == 'Description from dict'

def test_extract_description_fallback_empty():
    module = load_generate_feed_module()

    content = '<html><body><p>Nothing here either</p></body></html>'
    assert module._extract_description(content, 'test.html', {}) == ''

def test_atom_entry_escapes_url_and_id():
    module = load_generate_feed_module()

    mock_entry = {
        'title': 'Test Title',
        'url': 'https://example.com/page?param=1&other=<script>',
        'id': 'https://example.com/page?param=1&other=<script>',
        'updated': '2023-10-27T10:00:00Z',
        'summary': 'Test Summary',
        'preview_url': '',
    }

    entry_xml = module._atom_entry(mock_entry)

    assert 'https://example.com/page?param=1&amp;other=&lt;script&gt;' in entry_xml
    assert '<link href="https://example.com/page?param=1&amp;other=&lt;script&gt;" />' in entry_xml
    assert '<id>https://example.com/page?param=1&amp;other=&lt;script&gt;</id>' in entry_xml
    assert 'https://example.com/page?param=1&other=<script>' not in entry_xml

def test_build_feed_empty():
    from unittest.mock import patch
    from datetime import datetime, timezone

    module = load_generate_feed_module()

    with patch.object(module, 'datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2023, 10, 27, 10, 0, 0, tzinfo=timezone.utc)
        xml = module.build_feed([])

        assert '<?xml version="1.0" encoding="UTF-8"?>' in xml
        assert '<updated>2023-10-27T10:00:00Z</updated>' in xml
        assert '<entry>' not in xml

def test_build_feed_with_entries():
    module = load_generate_feed_module()

    entries = [
        {
            'title': 'Entry 1',
            'url': 'https://example.com/1',
            'id': 'https://example.com/1',
            'updated': '2023-10-25T10:00:00Z',
            'summary': 'Summary 1',
            'preview_url': 'https://example.com/1.png',
        },
        {
            'title': 'Entry 2',
            'url': 'https://example.com/2',
            'id': 'https://example.com/2',
            'updated': '2023-10-27T10:00:00Z',
            'summary': 'Summary 2',
            'preview_url': 'https://example.com/2.png',
        },
        {
            'title': 'Entry 3',
            'url': 'https://example.com/3',
            'id': 'https://example.com/3',
            'updated': '2023-10-26T10:00:00Z',
            'summary': 'Summary 3',
            'preview_url': 'https://example.com/3.png',
        }
    ]

    xml = module.build_feed(entries)

    # Check that feed_updated is the max of the updated timestamps
    assert '<updated>2023-10-27T10:00:00Z</updated>' in xml

    # Check that all entries are present
    assert '<title>Entry 1</title>' in xml
    assert '<title>Entry 2</title>' in xml
    assert '<title>Entry 3</title>' in xml
    assert xml.count('<entry>') == 3
