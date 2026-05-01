import importlib.util
from pathlib import Path


def load_generate_index_module():
    path = Path(__file__).parent.parent / 'deployment' / 'generate_index.py'
    spec = importlib.util.spec_from_file_location('generate_index', path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_inject_responsive_default_adds_v4_marker_and_canvas_rules():
    module = load_generate_index_module()
    initial_content = '<html><head></head><body><div class="grid"></div></body></html>'

    content = module.inject_responsive(initial_content, 'analysis.html')

    assert '<!-- responsive-inject-v5 -->' in content
    assert '.grid canvas { display: block; width: 100% !important; }' in content
    assert '.grid .small-card canvas { height: 190px !important; }' in content


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
        '</head>',
        '<body></body>',
        '</html>',
    ])

    content = module.inject_responsive(initial_content, 'analysis.html')

    assert '<!-- responsive-inject-v3 -->' not in content
    assert 'window.oldResponsive = true' not in content
    assert content.count('<!-- responsive-inject-v5 -->') == 1


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


def test_build_html_empty():
    module = load_generate_index_module()
    html = module.build_html([])

    assert 'No analyses yet — drop an HTML file here' in html
    assert '<div class="empty">No analyses found yet.' in html
    assert 'A hub for data analysis visualizations and insights.' in html


def test_build_html_single_analysis():
    module = load_generate_index_module()
    analysis = {
        'title': 'Test Analysis',
        'filename': 'test.html',
        'tags': ['test', 'single'],
        'description': 'A single test analysis.',
        'date': '2024-01-01',
    }

    html = module.build_html([analysis])

    assert '1 analysis</div>' in html or '<div class="header-sub">1 analysis</div>' in html
    assert '<div class="empty">No analyses found yet.' not in html
    assert '1 analysis from various datasets and projects.' in html
    assert 'Test Analysis' in html
    assert 'test.html' in html


def test_build_html_multiple_analyses():
    module = load_generate_index_module()
    analysis1 = {
        'title': 'Test Analysis 1',
        'filename': 'test1.html',
        'tags': ['test1'],
        'description': 'Test analysis one.',
        'date': '2024-01-01',
    }
    analysis2 = {
        'title': 'Test Analysis 2',
        'filename': 'test2.html',
        'tags': ['test2'],
        'description': 'Test analysis two.',
        'date': '2024-01-02',
    }

    html = module.build_html([analysis1, analysis2])

    assert '2 analyses</div>' in html or '<div class="header-sub">2 analyses</div>' in html
    assert '<div class="empty">No analyses found yet.' not in html
    assert '2 analyses from various datasets and projects.' in html
    assert 'Test Analysis 1' in html
    assert 'Test Analysis 2' in html


def test_main_with_none_skips_responsive_but_keeps_other_injections(tmp_path, monkeypatch):
    module = load_generate_index_module()
    analysis = tmp_path / 'sample.html'
    analysis.write_text(
        '<html><head><title>Sample</title></head><body><p>Hello</p></body></html>',
        encoding='utf-8',
    )

    monkeypatch.setattr(module, 'ROOT', tmp_path)
    monkeypatch.setattr(module, 'EXCLUDE', {'index.html'})

    module.main(['--responsive-preset', 'none'])

    content = analysis.read_text(encoding='utf-8')
    assert '<!-- responsive-inject-v5 -->' not in content
    assert module.BACK_LINK_MARKER in content
    assert 'og:image' in content
    assert (tmp_path / 'index.html').exists()
