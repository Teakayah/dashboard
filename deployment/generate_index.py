#!/usr/bin/env python3
"""
Generate index.html from all HTML analysis files in the repository root.
Run locally or via GitHub Actions on every push.
"""

import argparse
import json
import re
import subprocess
import random
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

ROOT = Path(__file__).parent.parent
EXCLUDE = {'index.html'}
SITE_URL = 'https://teakayah.github.io/dashboard'

# Visualization library detection patterns for card badges
LIBRARY_PATTERNS = {
    'Chart.js': r'chart\.js|chart\.umd',
    'D3.js': r'd3(?:\.v\d+)?(?:\.min)?\.js|cdn\.jsdelivr\.net/npm/d3@',
    'Plotly': r'plotly(?:\.min)?\.js|cdn\.plot\.ly',
    'Vega': r'vega(?:-lite)?(?:\.min)?\.js',
    'DuckDB': r'duckdb',
    'Grid.js': r'gridjs',
}

# Chart.js-inspired accent colors (top border on cards)
ACCENT_COLORS = [
    '#4f8ef7',  # blue
    '#ff6384',  # pink/red
    '#4bc0c0',  # teal
    '#ff9f40',  # orange
    '#9966ff',  # purple
    '#36a2eb',  # sky blue
    '#ffce56',  # yellow
    '#2ecc71',  # green
]


DESCRIPTIONS_FILE = ROOT / 'descriptions.json'


def load_descriptions() -> dict:
    """Load pre-generated AI descriptions from descriptions.json (committed to repo)."""
    if DESCRIPTIONS_FILE.exists():
        return json.loads(DESCRIPTIONS_FILE.read_text(encoding='utf-8'))
    return {}


def _git_date(filepath: Path) -> str:
    """Return 'Mon YYYY' from git log; fall back to mtime if the file isn't committed."""
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%ci', '--', str(filepath)],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        stamp = result.stdout.strip()
        if stamp:
            return datetime.fromisoformat(stamp).strftime('%b %Y')
    except Exception:
        pass
    return datetime.fromtimestamp(filepath.stat().st_mtime).strftime('%b %Y')


def extract_meta(filepath: Path, content: str, descriptions: Optional[dict] = None) -> dict:
    """Extract title, description, and tags from an HTML file content."""
    # Title
    title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else filepath.stem.replace('_', ' ').title()
    title = title.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&#39;', "'")

    # Meta description
    desc_match = re.search(
        r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']',
        content, re.IGNORECASE
    )
    description = desc_match.group(1).strip() if desc_match else ''

    if not description:
        sub_match = re.search(r'class=["\'][^"\']*subtitle[^"\']*["\'][^>]*>(.*?)</[a-z]+>', content, re.IGNORECASE | re.DOTALL)
        if sub_match:
            description = re.sub(r'<[^>]+>', '', sub_match.group(1)).strip()
            description = re.sub(r'\s+', ' ', description)
            if len(description) > 120:
                description = description[:117] + '…'

    if not description and descriptions:
        description = descriptions.get(filepath.name, '')

    tags = [name for name, pattern in LIBRARY_PATTERNS.items()
            if re.search(pattern, content, re.IGNORECASE)]

    date_str = _git_date(filepath)

    return {
        'filename': filepath.name,
        'title': title,
        'description': description,
        'tags': tags,
        'date': date_str,
    }


def _fallback(filepath: Path) -> dict:
    return {
        'filename': filepath.name,
        'title': filepath.stem.replace('_', ' ').title(),
        'description': '',
        'tags': [],
        'date': '',
    }


RESPONSIVE_PRESETS = {
    'default': {
        'marker': '<!-- responsive-inject-v5 -->',
        'snippet': '''\
  <!-- responsive-inject-v5 -->
  <style>
    @media (min-width: 769px) {
      body { max-width: 1200px; margin: 0 auto; }
      .panel > .card { height: 440px; }
      .grid canvas { display: block; width: 100% !important; }
      .grid .small-card canvas { height: 190px !important; }
    }
  </style>
  <script>
    (function () {
      if (window.innerWidth < 769) return;
      Object.defineProperty(window, 'Chart', {
        configurable: true,
        set: function (C) {
          Object.defineProperty(window, 'Chart', { configurable: true, writable: true, value: C });
          C.defaults.maintainAspectRatio = false;
        }
      });
    })();
  </script>
  <!-- /responsive-inject-v5 -->''',
    },
    'none': {
        'marker': None,
        'snippet': None,
    },
}


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.strip())
    parser.add_argument(
        '--responsive-preset',
        choices=sorted(RESPONSIVE_PRESETS),
        default='default',
        help='Responsive injection preset to apply to analysis pages.',
    )
    return parser.parse_args(argv)


def inject_responsive(content: str, filename: str, preset_name: str = 'default') -> str:
    """Inject responsive desktop layout enhancer into an analysis HTML file content."""
    preset = RESPONSIVE_PRESETS[preset_name]

    if preset_name == 'none':
        new_content = re.sub(
            r'\s*<!-- responsive-inject(?:-v\d+)? -->\s*<style>.*?</style>\s*<script>.*?</script>(?:\s*<!-- /responsive-inject(?:-v\d+)? -->)?',
            '',
            content,
            flags=re.DOTALL,
        )
        return new_content

    marker = preset['marker']
    snippet = preset['snippet']

    if marker in content:
        return content

    new_content = re.sub(
        r'\s*<!-- responsive-inject(?:-v\d+)? -->\s*<style>.*?</style>\s*<script>.*?</script>(?:\s*<!-- /responsive-inject(?:-v\d+)? -->)?',
        '',
        content,
        flags=re.DOTALL,
    )
    final_content = re.sub(
        r'(<head[^>]*>)',
        r'\1\n' + snippet,
        new_content,
        count=1,
        flags=re.IGNORECASE,
    )
    return final_content


THEME_LINK = '<link rel="stylesheet" href="assets/theme.css">'
FULLSCREEN_SCRIPT = '<script src="assets/fullscreen.js"></script>'
MANIFEST_LINK = '<link rel="manifest" href="manifest.json">'

def inject_assets(content: str, filename: str) -> str:
    """Inject theme CSS, manifest and utility JS into <head>."""
    if THEME_LINK in content:
        return content
    
    head_assets = f'\n  {THEME_LINK}\n  {FULLSCREEN_SCRIPT}\n  {MANIFEST_LINK}'
    new_content = re.sub(
        r'(</head>)',
        head_assets + r'\n\1',
        content,
        count=1,
        flags=re.IGNORECASE,
    )
    return new_content


HEADER_MARKER = '<!-- unified-header-inject -->'

def build_header_snippet() -> str:
    return f'''<!-- unified-header-inject -->
<header class="unified-header">
  <div class="back-link-box">
    <a href="{SITE_URL}/" style="font-weight:700; color:var(--primary); font-size:1.2rem;">DataDashboard</a>
    <span style="opacity:0.3; margin: 0 4px;">/</span>
    <a href="{SITE_URL}/" style="opacity:0.7;">Analyses</a>
  </div>
  <div class="nav-links">
    <button class="share-btn" onclick="navigator.share({{title: document.title, url: window.location.href}})">Share</button>
  </div>
</header>'''

def inject_unified_header(content: str, filename: str) -> str:
    """Inject a unified site header at the top of <body>."""
    if HEADER_MARKER in content:
        return content

    # Strip old back-link-inject block
    content = re.sub(r'<!-- back-link-inject -->.*?</div>', '', content, flags=re.DOTALL)

    header_snippet = build_header_snippet()
    new_content = re.sub(
        r'(<body[^>]*>)',
        r'\1\n' + header_snippet,
        content,
        count=1,
        flags=re.IGNORECASE,
    )
    return new_content


def inject_og_tags(content: str, filename: str, stem: str) -> str:
    """Inject og:image/twitter:image into an analysis HTML file content if not already present."""
    if 'og:image' in content:
        return content  # already has one, leave it alone

    image_url = f'{SITE_URL}/previews/{stem}.png'

    # Extract title for og:title
    title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else stem.replace('_', ' ').title()
    title = title.replace('&amp;', '&').replace('"', '&quot;')

    og_block = (
        f'\n  <!-- Open Graph / Social Sharing -->'
        f'\n  <meta property="og:type" content="article">'
        f'\n  <meta property="og:url" content="{SITE_URL}/{filename}">'
        f'\n  <meta property="og:title" content="{title}">'
        f'\n  <meta property="og:image" content="{image_url}">'
        f'\n  <meta property="og:image:width" content="600">'
        f'\n  <meta property="og:image:height" content="315">'
        f'\n  <meta property="twitter:card" content="summary_large_image">'
        f'\n  <meta property="twitter:image" content="{image_url}">'
    )

    # Insert just before </head>
    new_content = re.sub(r'(</head>)', og_block + r'\n\1', content, count=1, flags=re.IGNORECASE)
    return new_content


RELATED_MARKER = '<!-- related-links-inject -->'

def build_related_links(current_filename: str, all_meta: list[dict]) -> str:
    # Pick 3 random other analyses
    others = [m for m in all_meta if m['filename'] != current_filename]
    sample = random.sample(others, min(len(others), 3))
    
    links_html = "".join([
        f'<a href="{m["filename"]}" class="related-link"><strong>{m["title"]}</strong><span>{m["date"]}</span></a>'
        for m in sample
    ])

    return f'''<!-- related-links-inject -->
<section class="related-section">
  <div class="related-label">Related Analyses</div>
  <div class="related-grid">
    {links_html}
  </div>
</section>
<style>
  .related-section {{ padding: 40px 20px; border-top: 1px solid var(--border); background: #fafafa; margin-top: 60px; }}
  .related-label {{ font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: #999; margin-bottom: 16px; letter-spacing: 0.05em; text-align: center; }}
  .related-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; max-width: 1000px; margin: 0 auto; }}
  .related-link {{ display: flex; flex-direction: column; padding: 16px; background: #fff; border-radius: 10px; border: 1px solid var(--border); text-decoration: none; color: inherit; transition: transform 0.2s; }}
  .related-link:hover {{ transform: translateY(-3px); border-color: var(--primary); }}
  .related-link strong {{ font-size: 0.9rem; color: #1a1a2e; margin-bottom: 4px; }}
  .related-link span {{ font-size: 0.75rem; color: #bbb; }}
</style>'''

def inject_related_links(content: str, filename: str, all_meta: list[dict]) -> str:
    if RELATED_MARKER in content or len(all_meta) < 2:
        return content
    
    related_snippet = build_related_links(filename, all_meta)
    new_content = re.sub(
        r'(</body>)',
        related_snippet + r'\n\1',
        content,
        count=1,
        flags=re.IGNORECASE,
    )
    return new_content

def inject_pwa_script(content: str) -> str:
    if 'serviceWorker.register' in content:
        return content
    
    script = '''
  <script>
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js').then(reg => {
          console.log('SW registered:', reg);
        }).catch(err => {
          console.log('SW registration failed:', err);
        });
      });
    }
  </script>'''
    return re.sub(r'(</body>)', script + r'\n\1', content, count=1, flags=re.IGNORECASE)


def build_card(analysis: dict, index: int) -> str:
    color = ACCENT_COLORS[index % len(ACCENT_COLORS)]
    badges_html = ''.join(f'<span class="badge">{tag}</span>' for tag in analysis['tags'])
    desc_html = (
        f'<p class="card-desc">{analysis["description"]}</p>'
        if analysis['description'] else ''
    )
    date_html = (
        f'<div class="card-date">Last Updated: <span>{analysis["date"]}</span></div>'
        if analysis['date'] else ''
    )
    return f'''      <a class="card" href="{analysis['filename']}" style="--accent:{color}">
        <div class="card-top">
          <div class="card-title">{analysis['title']}</div>
          <div class="badges">{badges_html}</div>
        </div>
        {desc_html}
        <div class="card-footer">
          {date_html}
          <span class="card-link">Explore →</span>
        </div>
      </a>'''


def build_html(analyses: list[dict]) -> str:
    count = len(analyses)
    subtitle = f'{count} analysis{"" if count == 1 else "es"}' if count else 'A hub for interactive data insights'
    cards_html = '\n'.join(build_card(a, i) for i, a in enumerate(analyses))
    empty_html = '<div class="empty">No analyses found yet.</div>' if not analyses else ''
    og_image_url = f'{SITE_URL}/previews/index.png'
    og_desc = f'{count} analysis{"" if count == 1 else "es"} from various datasets and projects.'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DataDashboard</title>
  <meta property="og:type" content="website">
  <meta property="og:url" content="{SITE_URL}/">
  <meta property="og:title" content="DataDashboard">
  <meta property="og:description" content="{og_desc}">
  <meta property="og:image" content="{og_image_url}">
  <meta property="twitter:card" content="summary_large_image">
  <link rel="alternate" type="application/atom+xml" title="DataDashboard feed" href="{SITE_URL}/feed.xml">
  <link rel="stylesheet" href="assets/theme.css">
  <link rel="manifest" href="manifest.json">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ min-height: 100vh; }}
    header.hero {{ background: var(--header-bg); color: #fff; padding: 60px 32px 48px; text-align: center; }}
    header.hero h1 {{ font-size: 2.2rem; font-weight: 800; letter-spacing: -0.8px; margin-bottom: 8px; }}
    header.hero h1 span {{ color: var(--primary); }}
    .header-sub {{ font-size: 1rem; color: var(--header-muted); max-width: 600px; margin: 0 auto; }}
    .search-bar {{ padding: 0 32px; margin-top: -24px; display: flex; justify-content: center; }}
    .search-bar input {{ width: 100%; max-width: 600px; padding: 14px 20px; border-radius: 12px; border: 1px solid var(--border-dark); background: #fff; font-size: 0.95rem; color: #222; outline: none; box-shadow: 0 4px 12px rgba(0,0,0,0.08); transition: border-color 0.15s, box-shadow 0.15s; }}
    .search-bar input:focus {{ border-color: var(--primary); box-shadow: 0 0 0 4px rgba(79,142,247,0.15); }}
    main {{ padding: 48px 32px 64px; max-width: 1200px; margin: 0 auto; }}
    .grid-label {{ font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #999; margin-bottom: 20px; display: flex; align-items: center; gap: 12px; }}
    .grid-label::after {{ content: ""; height: 1px; background: var(--border); flex: 1; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 24px; }}
    .card {{ display: flex; flex-direction: column; background: #fff; border-radius: 16px; padding: 24px; box-shadow: 0 1px 6px rgba(0,0,0,0.05); border-top: 4px solid var(--accent, var(--primary)); text-decoration: none; color: inherit; transition: transform 0.2s, box-shadow 0.2s; }}
    .card:hover {{ transform: translateY(-4px); box-shadow: 0 12px 24px rgba(0,0,0,0.1); }}
    .card-title {{ font-size: 1.05rem; font-weight: 700; color: #1a1a2e; line-height: 1.4; margin-bottom: 8px; }}
    .badge {{ font-size: 0.65rem; font-weight: 700; color: var(--primary); background: rgba(79,142,247,0.1); border-radius: 6px; padding: 3px 8px; margin-right: 4px; }}
    .card-desc {{ font-size: 0.85rem; color: var(--text-muted); line-height: 1.6; margin-bottom: 20px; }}
    .card-footer {{ display: flex; align-items: center; justify-content: space-between; margin-top: auto; padding-top: 16px; border-top: 1px solid var(--border); }}
    .card-date {{ font-size: 0.72rem; color: #bbb; font-weight: 600; }}
    .card-date span {{ color: #999; }}
    .card-link {{ font-size: 0.8rem; font-weight: 700; color: var(--accent, var(--primary)); }}
    .card.hidden {{ display: none; }}
    footer {{ text-align: center; font-size: 0.8rem; color: #bbb; padding: 0 32px 48px; }}
    footer a {{ color: #999; text-decoration: none; font-weight: 600; }}
    footer a:hover {{ color: var(--primary); }}
    @media (max-width: 600px) {{ header.hero {{ padding: 40px 20px 32px; }} .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
<header class="hero">
  <h1>Data<span>Dashboard</span></h1>
  <div class="header-sub">{subtitle}</div>
</header>
<div class="search-bar">
  <input id="search" type="search" placeholder="Search analyses and tools…" autocomplete="off">
</div>
<main>
  <div class="grid-label">Available Analyses</div>
  <div class="grid" id="grid">{cards_html}</div>
  {empty_html}
</main>
<footer>
  <a href="https://github.com/Teakayah/dashboard" target="_blank" rel="noopener noreferrer">View on GitHub</a>
  &nbsp;·&nbsp;
  <a href="{SITE_URL}/feed.xml">RSS Feed</a>
</footer>
<script>
  const input = document.getElementById('search');
  const cards = document.querySelectorAll('.card');
  input.addEventListener('input', () => {{
    const q = input.value.trim().toLowerCase();
    cards.forEach(c => {{
      const text = c.textContent.toLowerCase();
      c.classList.toggle('hidden', q !== '' && !text.includes(q));
    }});
  }});
</script>
<script>
  if ('serviceWorker' in navigator) {{
    window.addEventListener('load', () => {{
      navigator.serviceWorker.register('/sw.js');
    }});
  }}
</script>
</body>
</html>'''


def main(argv: Optional[list[str]] = None):
    args = parse_args(argv)
    descriptions = load_descriptions()
    html_files = [p for p in ROOT.glob('*.html') if p.name.lower() not in EXCLUDE]
    html_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    
    all_meta = []
    for filepath in html_files:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
        all_meta.append(extract_meta(filepath, content, descriptions=descriptions))

    for filepath, meta in zip(html_files, all_meta):
        content = filepath.read_text(encoding='utf-8', errors='ignore')
        new_content = inject_assets(content, filepath.name)
        new_content = inject_responsive(new_content, filepath.name, args.responsive_preset)
        new_content = inject_unified_header(new_content, filepath.name)
        new_content = inject_og_tags(new_content, filepath.name, filepath.stem)
        new_content = inject_related_links(new_content, filepath.name, all_meta)
        new_content = inject_pwa_script(new_content)

        if new_content != content:
            filepath.write_text(new_content, encoding='utf-8')

    html = build_html(all_meta)
    (ROOT / 'index.html').write_text(html, encoding='utf-8')
    print(f'Generated index.html with {len(all_meta)} analyses.')

if __name__ == '__main__':
    main()
