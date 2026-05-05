import json
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import re

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

def test_load_descriptions_exists():
    module = load_generate_feed_module()
    mock_data = '{"test.html": "A description"}'
    with patch.object(module.Path, 'exists', return_value=True):
        with patch.object(module.Path, 'read_text', return_value=mock_data):
            assert module._load_descriptions() == {"test.html": "A description"}

def test_load_descriptions_not_exists():
    module = load_generate_feed_module()
    with patch.object(module.Path, 'exists', return_value=False):
        assert module._load_descriptions() == {}

def test_get_batched_git_isos_success():
    module = load_generate_feed_module()

    mock_result = MagicMock()
    mock_result.stdout = "TS:2023-10-27T10:00:00+00:00\ntest.html\n"

    mock_path = MagicMock(spec=Path)
    mock_path.name = "test.html"

    with patch('subprocess.run', return_value=mock_result):
        result = module._get_batched_git_isos([mock_path])
        assert result == {mock_path: "2023-10-27T10:00:00+00:00"}

def test_get_batched_git_isos_fallback():
    module = load_generate_feed_module()

    mock_path = MagicMock(spec=Path)
    mock_path.name = "test2.html"

    with patch('subprocess.run', side_effect=Exception("Git error")):
        result = module._get_batched_git_isos([mock_path])
        assert result == {}

def test_get_batched_git_isos_handles_git_failure():
    module = load_generate_feed_module()

    mock_path = MagicMock(spec=Path)
    mock_path.name = "dummy.html"

    with patch('subprocess.run', side_effect=Exception("git failed")):
        result = module._get_batched_git_isos([mock_path])
        assert result == {}

def test_git_iso_success():
    module = load_generate_feed_module()
    module._git_iso.cache_clear()

    mock_result = MagicMock()
    mock_result.stdout = "2023-10-27T10:00:00+00:00\n"

    with patch('subprocess.run', return_value=mock_result):
        assert module._git_iso(Path("test.html")) == "2023-10-27T10:00:00+00:00"

def test_build_entry_success():
    module = load_generate_feed_module()
    mock_path = MagicMock(spec=Path)
    mock_path.stem = "test_page"
    mock_path.name = "test_page.html"
    mock_path.read_text.return_value = '<html><head><title>Test Page</title></head><body></body></html>'

    entry = module._build_entry(mock_path, {"test_page.html": "desc"}, "2023-10-27T10:00:00Z")

    assert entry['title'] == "Test Page"
    assert entry['url'] == f"{module.SITE_URL}/test_page.html"
    assert entry['id'] == f"{module.SITE_URL}/test_page.html"
    assert entry['updated'] == "2023-10-27T10:00:00Z"
    assert entry['summary'] == "desc"
    assert entry['preview_url'] == f"{module.SITE_URL}/previews/test_page.png"

def test_build_entry_file_read_error():
    module = load_generate_feed_module()
    mock_path = MagicMock(spec=Path)
    mock_path.stem = "test_page"
    mock_path.name = "test_page.html"
    mock_path.read_text.side_effect = Exception("Read error")

    entry = module._build_entry(mock_path, {}, "2023-10-27T10:00:00Z")
    assert entry['title'] == "Test Page"  # fallback from stem

def test_build_feed_empty():
    module = load_generate_feed_module()
    feed = module.build_feed([])
    assert "<feed" in feed
    assert "<title>DataDashboard</title>" in feed
    assert "<entry>" not in feed

def test_build_feed_with_entries():
    module = load_generate_feed_module()
    entries = [{
        'title': 'Test',
        'url': 'http://test',
        'id': 'http://test',
        'updated': '2023-10-27T10:00:00Z',
        'summary': 'Summary',
        'preview_url': 'http://test/preview.png'
    }]
    feed = module.build_feed(entries)
    assert "<entry>" in feed
    assert "<title>Test</title>" in feed

def test_main():
    module = load_generate_feed_module()

    with patch.object(module, '_load_descriptions', return_value={}):
        with patch('pathlib.Path.glob') as mock_glob:
            mock_html = MagicMock(spec=Path)
            mock_html.name = "test.html"
            mock_html.stem = "test"
            mock_html.read_text.return_value = "<title>Test</title>"
            mock_glob.return_value = [mock_html]

            with patch.object(module, '_get_batched_git_isos', return_value={mock_html: "2023-10-27T10:00:00Z"}):
                with patch('pathlib.Path.write_text') as mock_write:
                    with patch('builtins.print'):
                        module.main()

                        mock_write.assert_called_once()
                        written_content = mock_write.call_args[0][0]
                        assert "<title>Test</title>" in written_content
