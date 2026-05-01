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

def test_build_html_empty_analyses():
    module = load_generate_index_module()
    html_output = module.build_html([])

    assert 'No analyses yet — drop an HTML file here' in html_output
    assert '<div class="empty">No analyses found yet.' in html_output
    assert 'A hub for data analysis visualizations and insights.' in html_output
    assert 'og:description' in html_output


def test_build_html_single_analysis():
    module = load_generate_index_module()
    analysis = {
        'filename': 'single.html',
        'title': 'Single Test Analysis',
        'tags': ['test', 'single'],
        'description': 'A test for a single analysis.',
        'date': '2023-10-01'
    }
    html_output = module.build_html([analysis])

    assert '1 analysis' in html_output
    assert '1 analysises' not in html_output
    assert 'Single Test Analysis' in html_output
    assert 'A test for a single analysis.' in html_output
    assert '<div class="empty">No analyses found yet.' not in html_output
    # Check OG description
    assert '1 analysis from various datasets and projects.' in html_output


def test_build_html_multiple_analyses():
    module = load_generate_index_module()
    analyses = [
        {
            'filename': 'first.html',
            'title': 'First Analysis',
            'tags': ['test1'],
            'description': 'Description one.',
            'date': '2023-10-01'
        },
        {
            'filename': 'second.html',
            'title': 'Second Analysis',
            'tags': ['test2'],
            'description': 'Description two.',
            'date': '2023-10-02'
        }
    ]
    html_output = module.build_html(analyses)

    assert '2 analysises' in html_output
    assert 'First Analysis' in html_output
    assert 'Second Analysis' in html_output
    assert '<div class="empty">No analyses found yet.' not in html_output
    assert '2 analysises from various datasets and projects.' in html_output
