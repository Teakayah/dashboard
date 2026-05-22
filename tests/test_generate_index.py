import importlib.util
from pathlib import Path
from unittest.mock import patch
import pytest


def load_generate_index_module():
    path = Path(__file__).parent.parent / 'deployment' / 'generate_index.py'
    spec = importlib.util.spec_from_file_location('generate_index', path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_inject_responsive_default_adds_v6_marker_and_dashboard_rules():
    module = load_generate_index_module()
    initial_content = '<html><head></head><body><div class="grid"></div></body></html>'

    content = module.inject_responsive(initial_content, 'analysis.html')

    assert '<!-- responsive-inject-v6 -->' in content
    assert '.dashboard-container { display: flex; flex-direction: row; }' in content
    assert 'Object.defineProperty(window, \'Chart\'' in content


def test_inject_responsive_is_idempotent():
    module = load_generate_index_module()
    initial_content = '<html><head></head><body></body></html>'

    first = module.inject_responsive(initial_content, 'analysis.html')
    second = module.inject_responsive(first, 'analysis.html')

    assert first == second
    assert second.count('<!-- responsive-inject-v6 -->') == 1


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
    assert content.count('<!-- responsive-inject-v6 -->') == 1


def test_strip_back_link_removes_existing():
    module = load_generate_index_module()
    snippet = ('<!-- back-link-inject -->'
               '<div style="x"><a href="/">&#8592; DataDashboard</a></div>')
    content = f'<html><body>\n{snippet}\n<h1>Test</h1></body></html>'
    res = module.strip_back_link(content, 'test.html')
    assert '<!-- back-link-inject -->' not in res
    assert '<h1>Test</h1>' in res


def test_strip_back_link_no_op_when_absent():
    module = load_generate_index_module()
    content = '<html><body><h1>Test</h1></body></html>'
    assert module.strip_back_link(content, 'test.html') == content


def test_strip_back_link_is_idempotent():
    module = load_generate_index_module()
    snippet = ('<!-- back-link-inject -->'
               '<div style="x"><a href="/">&#8592; DataDashboard</a></div>')
    content = f'<html><body>\n{snippet}\n<h1>Test</h1></body></html>'
    first = module.strip_back_link(content, 'test.html')
    second = module.strip_back_link(first, 'test.html')
    assert first == second


def test_inject_favicon_adds_link(monkeypatch):
    module = load_generate_index_module()
    monkeypatch.setattr(module, 'SITE_URL', 'https://testsite.com')

    # Normal head
    content = '<html><head></head><body><h1>Test</h1></body></html>'
    res = module.inject_favicon(content, 'test.html')
    assert 'rel="icon"' in res
    assert 'https://testsite.com/favicon.ico' in res
    assert res.startswith('<html><head>\n  <link rel="icon" href="https://testsite.com/favicon.ico" type="image/x-icon">\n</head>')

    # Head with attributes
    content = '<html><head class="my-class"></head><body><h1>Test</h1></body></html>'
    res = module.inject_favicon(content, 'test.html')
    assert 'rel="icon"' in res
    assert res.startswith('<html><head class="my-class">\n  <link rel="icon" href="https://testsite.com/favicon.ico" type="image/x-icon">\n</head>')


def test_inject_favicon_is_idempotent(monkeypatch):
    module = load_generate_index_module()
    monkeypatch.setattr(module, 'SITE_URL', 'https://testsite.com')
    initial_content = '<html><head></head><body><h1>Test</h1></body></html>'

    first = module.inject_favicon(initial_content, 'test.html')
    second = module.inject_favicon(first, 'test.html')

    assert first == second
    assert second.count('rel="icon"') == 1

    # Works with single quotes too
    third_content = "<html><head>\n  <link rel='icon' href='favicon.ico'>\n</head><body></body></html>"
    fourth = module.inject_favicon(third_content, 'test.html')
    assert fourth == third_content


def test_inject_share_fix_replaces_unsafe_handler():
    module = load_generate_index_module()

    unsafe = 'onclick="navigator.share({title: document.title, url: window.location.href})"'
    content = f'<html><body><button {unsafe}>Share</button></body></html>'
    res = module.inject_share_fix(content, 'test.html')
    assert unsafe not in res
    assert 'navigator.share' in res
    assert 'navigator.clipboard' in res


def test_inject_share_fix_is_idempotent():
    module = load_generate_index_module()

    unsafe = 'onclick="navigator.share({title: document.title, url: window.location.href})"'
    content = f'<html><body><button {unsafe}>Share</button></body></html>'
    first = module.inject_share_fix(content, 'test.html')
    second = module.inject_share_fix(first, 'test.html')
    assert first == second


def test_inject_share_fix_no_op_when_absent():
    module = load_generate_index_module()
    content = '<html><body><p>No share button here</p></body></html>'
    assert module.inject_share_fix(content, 'test.html') == content


def test_inject_contrast_fix_adds_style():
    module = load_generate_index_module()
    content = '<html><head></head><body><p>Hello</p></body></html>'
    res = module.inject_contrast_fix(content, 'test.html')
    assert 'data-contrast-fix' in res
    assert 'var(--bg)' in res
    assert 'var(--text)' in res


def test_inject_contrast_fix_is_idempotent():
    module = load_generate_index_module()
    content = '<html><head></head><body><p>Hello</p></body></html>'
    first = module.inject_contrast_fix(content, 'test.html')
    second = module.inject_contrast_fix(first, 'test.html')
    assert first == second
    assert second.count('data-contrast-fix') == 1


def test_inject_functions_handle_missing_tags():
    module = load_generate_index_module()
    content_no_tags = "<html><body>No head here</body></html>"

    # inject_responsive expects <head>
    res1 = module.inject_responsive(content_no_tags, "test.html")
    assert res1 == content_no_tags
    assert isinstance(res1, str)

    content_no_body = "<html><head></head>No body here</html>"
    # strip_back_link is a no-op when marker is absent
    res2 = module.strip_back_link(content_no_body, "test.html")
    assert res2 == content_no_body
    assert isinstance(res2, str)

    # inject_og_tags expects </head>
    res3 = module.inject_og_tags(content_no_tags, "test.html", "test")
    assert res3 == content_no_tags
    assert isinstance(res3, str)

    # inject_favicon expects </head>
    res4 = module.inject_favicon(content_no_tags, "test.html")
    assert res4 == content_no_tags
    assert isinstance(res4, str)


def test_inject_responsive_returns_early_if_marker_present():
    module = load_generate_index_module()
    content = "<html><head><!-- responsive-inject-v6 --></head><body></body></html>"
    res = module.inject_responsive(content, "test.html")
    assert res == content
    assert isinstance(res, str)


def test_strip_analysis_utils_removes_tag():
    module = load_generate_index_module()
    content = '<html><head><script src="assets/analysis_utils.js"></script></head><body></body></html>'
    res = module.strip_analysis_utils(content, 'test.html')
    assert 'analysis_utils.js' not in res
    assert '<head>' in res


def test_strip_analysis_utils_is_idempotent():
    module = load_generate_index_module()
    content = '<html><head><script src="assets/analysis_utils.js"></script></head><body></body></html>'
    first = module.strip_analysis_utils(content, 'test.html')
    second = module.strip_analysis_utils(first, 'test.html')
    assert first == second


def test_strip_analysis_utils_no_op_when_absent():
    module = load_generate_index_module()
    content = '<html><head></head><body><p>No utils here</p></body></html>'
    assert module.strip_analysis_utils(content, 'test.html') == content


def test_strip_analysis_utils_handles_single_quotes():
    module = load_generate_index_module()
    content = "<html><head><script src='assets/analysis_utils.js'></script></head><body></body></html>"
    res = module.strip_analysis_utils(content, 'test.html')
    assert 'analysis_utils.js' not in res


def test_inject_og_tags_adds_tags_with_extracted_title(monkeypatch):
    module = load_generate_index_module()
    monkeypatch.setattr(module, 'SITE_URL', 'https://testsite.com')
    content = "<html><head><title>   Test Title   </title></head><body></body></html>"
    res = module.inject_og_tags(content, "analysis.html", "analysis_stem")

    assert '<meta property="og:title" content="Test Title">' in res
    assert '<meta property="og:image" content="https://testsite.com/previews/analysis_stem.png">' in res
    assert '<meta property="og:url" content="https://testsite.com/analysis.html">' in res
    assert '<meta property="twitter:image" content="https://testsite.com/previews/analysis_stem.png">' in res


def test_inject_og_tags_adds_tags_with_stem_fallback(monkeypatch):
    module = load_generate_index_module()
    monkeypatch.setattr(module, 'SITE_URL', 'https://testsite.com')
    content = "<html><head></head><body></body></html>"
    res = module.inject_og_tags(content, "analysis.html", "my_cool_analysis")

    # Stem is formatted with `.replace('_', ' ').title()`
    assert '<meta property="og:title" content="My Cool Analysis">' in res
    assert '<meta property="og:image" content="https://testsite.com/previews/my_cool_analysis.png">' in res


def test_inject_og_tags_leaves_existing_og_image_alone():
    module = load_generate_index_module()
    content = '<html><head><meta property="og:image" content="some_img.png"></head><body></body></html>'
    res = module.inject_og_tags(content, "analysis.html", "analysis_stem")

    assert res == content
    assert '<!-- Open Graph / Social Sharing -->' not in res


def test_inject_og_tags_escapes_title(monkeypatch):
    module = load_generate_index_module()
    monkeypatch.setattr(module, 'SITE_URL', 'https://testsite.com')
    content = '<html><head><title>Title with "quotes" and <tags></title></head><body></body></html>'
    res = module.inject_og_tags(content, "analysis.html", "analysis_stem")

    # Title will have quotes escaped correctly as well as tags unescaped then escaped
    assert '<meta property="og:title" content="Title with &quot;quotes&quot; and &lt;tags&gt;">' in res


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
    assert '<!-- responsive-inject-v6 -->' not in content
    assert module.BACK_LINK_MARKER not in content
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
        <script src="https://cdn.jsdelivr.net/npm/chart.js" integrity="sha384-mock" crossorigin="anonymous"></script>
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


def test_extract_meta_html_entities():
    module = load_generate_index_module()
    content = """
    <html>
    <head>
        <title>Tom &amp; Jerry</title>
        <meta name="description" content="Cat &amp; Mouse">
    </head>
    <body></body>
    </html>
    """
    filepath = Path('test_file.html')
    result = module.extract_meta(filepath, content)

    assert result['title'] == 'Tom & Jerry'
    assert result['description'] == 'Cat & Mouse'


def test_extract_meta_subtitle_nested_tags():
    module = load_generate_index_module()
    content = """
    <html>
    <head>
        <title>Subtitle Test</title>
    </head>
    <body>
        <h2 class="subtitle">
            This <b>is</b> a test
            <span>with newlines</span>
        </h2>
    </body>
    </html>
    """
    filepath = Path('test_file.html')
    result = module.extract_meta(filepath, content)

    assert result['description'] == 'This is a test with newlines'


def test_extract_meta_multiple_tags():
    module = load_generate_index_module()
    content = """
    <html>
    <head>
        <title>Tags Test</title>
    </head>
    <body>
        <script src="https://cdn.jsdelivr.net/npm/chart.js" integrity="sha384-mock" crossorigin="anonymous"></script>
        <script src="https://cdn.plot.ly/plotly-latest.min.js" integrity="sha384-mock2" crossorigin="anonymous"></script>
    </body>
    </html>
    """
    filepath = Path('test_file.html')
    result = module.extract_meta(filepath, content)

    assert 'Chart.js' in result['tags']
    assert 'Plotly' in result['tags']
    assert len(result['tags']) == 2


def test__fallback_function():
    module = load_generate_index_module()
    filepath = Path('some_test_file.html')

    result = module._fallback(filepath, date_str='May 2024')

    assert result['filename'] == 'some_test_file.html'
    assert result['title'] == 'Some Test File'
    assert result['description'] == ''
    assert result['tags'] == []
    assert result['date'] == 'May 2024'


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


def test_build_html_empty_analyses():
    module = load_generate_index_module()
    html = module.build_html([])

    assert 'No analyses found yet' in html
    assert 'No analyses yet — drop an HTML file here' in html
    assert 'class="card"' not in html
    assert 'class="empty"' in html


def test_build_html_with_analyses(monkeypatch):
    module = load_generate_index_module()

    # Mock SITE_URL and ACCENT_COLORS to ensure consistent output
    monkeypatch.setattr(module, 'SITE_URL', 'https://example.com')
    monkeypatch.setattr(module, 'ACCENT_COLORS', ['#ff0000', '#00ff00'])

    analyses = [
        {
            'filename': 'analysis1.html',
            'title': 'Analysis One',
            'description': 'The first analysis description',
            'tags': ['Chart.js', 'Stats'],
            'date': 'Jan 2024'
        },
        {
            'filename': 'analysis2.html',
            'title': 'Analysis Two',
            'description': '', # Test empty description
            'tags': [], # Test empty tags
            'date': '' # Test empty date
        }
    ]

    html = module.build_html(analyses)

    # Check subtitle
    assert '2 analyses' in html
    assert 'from various datasets and projects' in html

    # Check empty state is NOT present
    assert 'No analyses found yet' not in html
    assert 'class="empty"' not in html

    # Check Card 1 details
    assert 'analysis1.html' in html
    assert 'Analysis One' in html
    assert 'The first analysis description' in html
    assert 'Chart.js' in html
    assert 'Stats' in html
    assert 'Jan 2024' in html

    # Check Card 2 details
    assert 'analysis2.html' in html
    assert 'Analysis Two' in html

    # Count cards
    assert html.count('class="card"') == 2


def test_build_html_single_analysis(monkeypatch):
    module = load_generate_index_module()

    # Mock SITE_URL and ACCENT_COLORS
    monkeypatch.setattr(module, 'SITE_URL', 'https://example.com')
    monkeypatch.setattr(module, 'ACCENT_COLORS', ['#ff0000'])

    analyses = [
        {
            'filename': 'single.html',
            'title': 'Single Analysis',
            'description': 'Only one',
            'tags': ['DuckDB'],
            'date': 'Feb 2024'
        }
    ]

    html = module.build_html(analyses)

    # Check singular subtitle
    assert '1 analysis' in html
    assert '1 analysis from various' in html

    # Verify card exists
    assert 'single.html' in html
    assert 'Single Analysis' in html
    assert html.count('class="card"') == 1


def test_build_card_fully_populated():
    module = load_generate_index_module()
    analysis = {
        'title': 'Test Analysis',
        'description': 'A description',
        'date': '2023-01-01',
        'filename': 'test.html',
        'tags': ['tag1', 'tag2']
    }
    html = module.build_card(analysis, 0)
    assert 'Test Analysis' in html
    assert 'A description' in html
    assert '2023-01-01' in html
    assert 'href="test.html"' in html
    assert '>tag1<' in html
    assert '>tag2<' in html
    assert '--accent:' in html


def test_build_card_missing_optional_fields():
    module = load_generate_index_module()
    analysis = {
        'title': 'Minimal Analysis',
        'description': '',
        'date': None,
        'filename': 'min.html',
        'tags': []
    }
    html = module.build_card(analysis, 1)
    assert 'Minimal Analysis' in html
    assert 'href="min.html"' in html
    assert 'card-desc' not in html
    assert 'card-date' not in html


def test_build_card_html_escaping():
    module = load_generate_index_module()
    analysis = {
        'title': '<script>alert("xss")</script>',
        'description': 'Description with "quotes" and &ampersand',
        'date': '2023-01-01 <script>',
        'filename': 'evil"file.html',
        'tags': ['<tag>']
    }
    html = module.build_card(analysis, 2)
    assert '<script>' not in html
    assert '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;' in html
    assert 'Description with &quot;quotes&quot; and &amp;ampersand' in html
    assert '2023-01-01 &lt;script&gt;' in html
    assert 'evil&quot;file.html' in html
    assert '&lt;tag&gt;' in html


def test_parse_args_default():
    module = load_generate_index_module()
    args = module.parse_args([])
    assert args.responsive_preset == 'default'


def test_parse_args_none():
    module = load_generate_index_module()
    args = module.parse_args(['--responsive-preset', 'none'])
    assert args.responsive_preset == 'none'


def test_parse_args_invalid():
    module = load_generate_index_module()
    with pytest.raises(SystemExit):
        module.parse_args(['--responsive-preset', 'invalid_choice'])
