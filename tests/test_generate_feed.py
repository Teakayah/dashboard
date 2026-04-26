import importlib.util
from pathlib import Path

def load_generate_feed_module():
    path = Path(__file__).parent.parent / 'deployment' / 'generate_feed.py'
    spec = importlib.util.spec_from_file_location('generate_feed', path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

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
