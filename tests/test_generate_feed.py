import importlib.util
from pathlib import Path

def load_generate_feed_module():
    path = Path(__file__).parent.parent / 'deployment' / 'generate_feed.py'
    spec = importlib.util.spec_from_file_location('generate_feed', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

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
