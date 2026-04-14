import importlib.util
from pathlib import Path


def load_generate_index_module():
    path = Path(__file__).parent.parent / 'deployment' / 'generate_index.py'
    spec = importlib.util.spec_from_file_location('generate_index', path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_inject_responsive_default_adds_v4_marker_and_canvas_rules(tmp_path):
    module = load_generate_index_module()
    html = tmp_path / 'analysis.html'
    html.write_text('<html><head></head><body><div class="grid"></div></body></html>', encoding='utf-8')

    module.inject_responsive(html)

    content = html.read_text(encoding='utf-8')
    assert '<!-- responsive-inject-v4 -->' in content
    assert '.grid canvas { display: block; width: 100% !important; }' in content
    assert '.grid .small-card canvas { height: 190px !important; }' in content


def test_inject_responsive_is_idempotent(tmp_path):
    module = load_generate_index_module()
    html = tmp_path / 'analysis.html'
    html.write_text('<html><head></head><body></body></html>', encoding='utf-8')

    module.inject_responsive(html)
    first = html.read_text(encoding='utf-8')
    module.inject_responsive(html)
    second = html.read_text(encoding='utf-8')

    assert first == second
    assert second.count('<!-- responsive-inject-v4 -->') == 1


def test_inject_responsive_replaces_older_versions(tmp_path):
    module = load_generate_index_module()
    html = tmp_path / 'analysis.html'
    html.write_text(
        '\n'.join([
            '<html>',
            '<head>',
            '  <!-- responsive-inject-v3 -->',
            '  <style>.old { color: red; }</style>',
            '  <script>window.oldResponsive = true;</script>',
            '</head>',
            '<body></body>',
            '</html>',
        ]),
        encoding='utf-8',
    )

    module.inject_responsive(html)

    content = html.read_text(encoding='utf-8')
    assert '<!-- responsive-inject-v3 -->' not in content
    assert 'window.oldResponsive = true' not in content
    assert content.count('<!-- responsive-inject-v4 -->') == 1


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
    assert '<!-- responsive-inject-v4 -->' not in content
    assert module.BACK_LINK_MARKER in content
    assert 'og:image' in content
    assert (tmp_path / 'index.html').exists()
