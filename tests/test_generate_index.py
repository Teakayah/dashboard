import importlib.util
from pathlib import Path
from unittest.mock import patch


def load_generate_index_module():
    path = Path(__file__).parent.parent / 'deployment' / 'generate_index.py'
    spec = importlib.util.spec_from_file_location('generate_index', path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_inject_responsive_default_adds_v5_marker_and_dashboard_rules():
    module = load_generate_index_module()
    initial_content = '<html><head></head><body><div class="grid"></div></body></html>'

    content = module.inject_responsive(initial_content, 'analysis.html')

    assert '<!-- responsive-inject-v5 -->' in content
    assert '.dashboard-container { display: flex; flex-direction: row; }' in content
    assert 'window.Chart' in content


def test_inject_responsive_is_idempotent():
    module = load_generate_index_module()
    initial_content = '<html><head></head><body></body></html>'

    first = module.inject_responsive(initial_content, 'analysis.html')
    second = module.inject_responsive(first, 'analysis.html')

    assert first == second
    assert second.count('<!-- responsive-inject-v5 -->') == 1


def test_inject_responsive_replaces_older_versions():
    module = load_generate_index_module()
    initial_content = '\n'.join([
        '<html>',
        '<head>',
        '  <!-- responsive-inject-v3 -->',
        '  <style>.old { color: red; }</style>',
        '  <script>window.oldResponsive = true;</script>',
        '  <!-- /responsive-inject-v3 -->',
        '</head>',
        '<body></body>',
        '</html>',
    ])
    content = module.inject_responsive(initial_content, 'analysis.html')

    assert '<!-- responsive-inject-v3 -->' not in content
    assert 'window.oldResponsive = true' not in content
    assert content.count('<!-- responsive-inject-v5 -->') == 1


def test_inject_back_link_adds_snippet():
    module = load_generate_index_module()
    content = "<html><head></head><body>\n<h1>Hello</h1>\n</body></html>"
    result = module.inject_back_link(content, "test.html")

    assert result != content
    assert module.BACK_LINK_MARKER in result
    assert "<body>\n<!-- back-link-inject -->" in result


def test_inject_back_link_is_idempotent():
    module = load_generate_index_module()
    content = f"<html><head></head><body>\n{module.BACK_LINK_SNIPPET}\n<h1>Hello</h1>\n</body></html>"

    result = module.inject_back_link(content, "test.html")
    assert result == content


def test_inject_back_link_handles_body_attributes():
    module = load_generate_index_module()
    content = '<html><head></head><body class="bg-gray-100" id="main">\n<h1>Hello</h1>\n</body></html>'
    result = module.inject_back_link(content, "test.html")

    assert result != content
    assert module.BACK_LINK_MARKER in result
    assert '<body class="bg-gray-100" id="main">\n<!-- back-link-inject -->' in result


def test_inject_functions_handle_missing_tags():
    module = load_generate_index_module()
    content_no_tags = "<html><body>No head here</body></html>"

    # inject_responsive expects <head>
    res1 = module.inject_responsive(content_no_tags, "test.html")
    assert res1 == content_no_tags
    assert isinstance(res1, str)

    content_no_body = "<html><head></head>No body here</html>"
    # inject_back_link expects <body>
    res2 = module.inject_back_link(content_no_body, "test.html")
    assert res2 == content_no_body
    assert isinstance(res2, str)

    # inject_og_tags expects </head>
    res3 = module.inject_og_tags(content_no_tags, "test.html", "test")
    assert res3 == content_no_tags
    assert isinstance(res3, str)


def test_main_with_none_skips_responsive_but_keeps_other_injections(tmp_path, monkeypatch):
    module = load_generate_index_module()
    analysis = tmp_path / 'sample.html'
    analysis.write_text(
        '<html><head><title>Sample</title></head><body><p>Hello</p></body></html>',
        encoding='utf-8',
    )

    monkeypatch.setattr(module, 'ROOT', tmp_path)
    monkeypatch.setattr(module, 'EXCLUDE', {'index.html'})

    # Mock get_git_dates_batched to avoid subprocess calls during test
    with patch.object(module, 'get_git_dates_batched', return_value={analysis: 'May 2026'}):
        module.main(['--responsive-preset', 'none'])

    content = analysis.read_text(encoding='utf-8')
    assert '<!-- responsive-inject-v5 -->' not in content
    assert module.BACK_LINK_MARKER in content
    assert 'og:image' in content
    assert (tmp_path / 'index.html').exists()


def test_extract_meta_basic():
    module = load_generate_index_module()
    content = """
    <html>
    <head>
        <title>Test Title</title>
        <meta name="description" content="Test Description">
    </head>
    <body>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </body>
    </html>
    """
    filepath = Path('test_file.html')
    result = module.extract_meta(filepath, content, git_date='Jan 2023')

    assert result['filename'] == 'test_file.html'
    assert result['title'] == 'Test Title'
    assert result['description'] == 'Test Description'
    assert 'Chart.js' in result['tags']
    assert result['date'] == 'Jan 2023'


def test_extract_meta_fallback_subtitle_truncation():
    module = load_generate_index_module()
    long_subtitle = "This is a very long subtitle that should definitely exceed the one hundred and twenty character limit imposed by the extract meta function in order to test the truncation logic properly."
    content = f"""
    <html>
    <head>
        <title>Subtitle Test</title>
    </head>
    <body>
        <h2 class="some-class subtitle extra-class">{long_subtitle}</h2>
    </body>
    </html>
    """
    filepath = Path('test_file.html')
    result = module.extract_meta(filepath, content, git_date='Feb 2023')

    assert result['title'] == 'Subtitle Test'
    assert len(result['description']) == 118 # 117 chars + '…'
    assert result['description'].endswith('…')
    assert result['description'] == long_subtitle[:117] + '…'


def test_extract_meta_fallback_descriptions_dict():
    module = load_generate_index_module()
    content = """
    <html>
    <head>
        <title>Descriptions Dict Test</title>
    </head>
    <body>
    </body>
    </html>
    """
    filepath = Path('test_file.html')
    descriptions = {'test_file.html': 'Description from dict'}
    result = module.extract_meta(filepath, content, descriptions=descriptions, git_date='Mar 2023')

    assert result['description'] == 'Description from dict'


def test_extract_meta_fallback_stem_title():
    module = load_generate_index_module()
    content = """
    <html>
    <head>
    </head>
    <body>
    </body>
    </html>
    """
    filepath = Path('my_test_file.html')
    result = module.extract_meta(filepath, content, git_date='Apr 2023')

    assert result['title'] == 'My Test File'


def test_get_git_dates_batched_empty_list():
    module = load_generate_index_module()
    assert module.get_git_dates_batched([]) == {}


def test_get_git_dates_batched_success(monkeypatch, tmp_path):
    module = load_generate_index_module()
    monkeypatch.setattr(module, 'ROOT', tmp_path)

    file1 = tmp_path / 'file1.txt'
    file1.touch()

    class MockResult:
        stdout = "TS:2023-01-15T10:00:00+00:00\nfile1.txt\n"

    def mock_run(*args, **kwargs):
        return MockResult()

    monkeypatch.setattr(module.subprocess, 'run', mock_run)

    dates = module.get_git_dates_batched([file1])
    assert dates == {file1: 'Jan 2023'}


def test_get_git_dates_batched_fallback_mtime(monkeypatch, tmp_path):
    module = load_generate_index_module()
    monkeypatch.setattr(module, 'ROOT', tmp_path)

    file1 = tmp_path / 'file2.txt'
    file1.touch()

    # Force exception in git log command
    def mock_run(*args, **kwargs):
        raise Exception("Git command failed")

    monkeypatch.setattr(module.subprocess, 'run', mock_run)

    dates = module.get_git_dates_batched([file1])
    assert file1 in dates
    assert isinstance(dates[file1], str)


def test_load_descriptions_exists(monkeypatch, tmp_path):
    module = load_generate_index_module()
    monkeypatch.setattr(module, 'DESCRIPTIONS_FILE', tmp_path / 'descriptions.json')
    (tmp_path / 'descriptions.json').write_text('{"file1.html": "description1"}', encoding='utf-8')
    assert module.load_descriptions() == {"file1.html": "description1"}


def test_load_descriptions_not_exists(monkeypatch, tmp_path):
    module = load_generate_index_module()
    monkeypatch.setattr(module, 'DESCRIPTIONS_FILE', tmp_path / 'descriptions_missing.json')
    assert module.load_descriptions() == {}
