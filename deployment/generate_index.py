#!/usr/bin/env python3
"""
Generate index.html from all HTML analysis files in the repository root.
Run locally or via GitHub Actions on every push.
"""

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
EXCLUDE = {'index.html'}
SITE_URL = 'https://teakayah.github.io/dashboard'

# Visualization library detection patterns for card badges
LIBRARY_PATTERNS = {
    'Chart.js': r'chart\.js|chart\.umd',
    'D3.js': r'd3(?:\.v\d+)?(?:\.min)?\.js|cdn\.jsdelivr\.net/npm/d3@',
    'Plotly': r'plotly(?:\.min)?\.js|cdn\.plot\.ly',
    'Vega': r'vega(?:-lite)?(?:\.min)?\.js',
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


def extract_meta(filepath: Path, descriptions: dict | None = None) -> dict:
    """Extract title, description, and tags from an HTML file.

    Falls back to pre-generated descriptions from descriptions.json when no
    <meta name="description"> or subtitle element is found in the HTML.
    """
    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return _fallback(filepath)

    # Title
    title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else filepath.stem.replace('_', ' ').title()
    # Clean HTML entities in title
    title = title.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&#39;', "'")

    # Meta description
    desc_match = re.search(
        r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']',
        content, re.IGNORECASE
    )
    description = desc_match.group(1).strip() if desc_match else ''

    # If no meta description, look for a subtitle element (common pattern in your files)
    if not description:
        sub_match = re.search(r'class=["\'][^"\']*subtitle[^"\']*["\'][^>]*>(.*?)</[a-z]+>', content, re.IGNORECASE | re.DOTALL)
        if sub_match:
            description = re.sub(r'<[^>]+>', '', sub_match.group(1)).strip()
            description = re.sub(r'\s+', ' ', description)
            if len(description) > 120:
                description = description[:117] + '…'

    # Fallback: use pre-generated description from descriptions.json
    if not description and descriptions:
        description = descriptions.get(filepath.name, '')

    # Detect visualization libraries
    tags = [name for name, pattern in LIBRARY_PATTERNS.items()
            if re.search(pattern, content, re.IGNORECASE)]

    # Date from git log (CI-safe; mtime is always "now" after checkout)
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


def get_analyses() -> list[dict]:
    descriptions = load_descriptions()
    analyses = []
    for html_file in sorted(ROOT.glob('*.html'), key=lambda p: p.stat().st_mtime, reverse=True):
        if html_file.name.lower() in EXCLUDE:
            continue
        analyses.append(extract_meta(html_file, descriptions=descriptions))
    return analyses


RESPONSIVE_PRESETS = {
    'default': {
        'marker': '<!-- responsive-inject-v4 -->',
        'snippet': '''\
  <!-- responsive-inject-v4 -->
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
  <!-- /responsive-inject -->''',
    },
    'none': {
        'marker': None,
        'snippet': None,
    },
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.strip())
    parser.add_argument(
        '--responsive-preset',
        choices=sorted(RESPONSIVE_PRESETS),
        default='default',
        help='Responsive injection preset to apply to analysis pages.',
    )
    return parser.parse_args(argv)


def inject_responsive(content: str, filename: str, preset_name: str = 'default') -> str:
    """Inject responsive desktop layout enhancer into an analysis HTML file content.

    Injected right after <head> so the Chart.js defineProperty trap runs
    before chart.js itself is loaded (which typically appears in <head>).
    Strips any older version of the injection before re-injecting.
    """
    preset = RESPONSIVE_PRESETS[preset_name]

    new_content = re.sub(
        r'\s*<!-- responsive-inject(?:-v\d+)? -->\s*<style>.*?</style>\s*<script>.*?</script>(?:\s*<!-- /responsive-inject -->)?',
        '',
        content,
        flags=re.DOTALL,
    )
    if preset_name == 'none':
        if new_content != content:
            print(f'  Removed responsive enhancer from {filename}')
        return new_content

    marker = preset['marker']
    snippet = preset['snippet']
    if marker in new_content:
        return new_content  # already up to date

    # Inject right after <head> so our script runs before chart.js loads
    final_content = re.sub(
        r'(<head[^>]*>)',
        r'\1\n' + snippet,
        new_content,
        count=1,
        flags=re.IGNORECASE,
    )
    if final_content != new_content:
        print(f'  Injected responsive enhancer into {filename}')
    return final_content


BACK_LINK_MARKER = '<!-- back-link-inject -->'

BACK_LINK_SNIPPET = (
    '<!-- back-link-inject -->'
    '<div style="font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif;'
    'padding:6px 0 2px;font-size:0.78rem;">'
    f'<a href="{SITE_URL}/" style="color:#4f8ef7;text-decoration:none;font-weight:600;">'
    '&#8592; DataDashboard</a></div>'
)


def inject_back_link(content: str, filename: str) -> str:
    """Inject a 'back to homepage' link right after <body> in an analysis file content."""
    if BACK_LINK_MARKER in content:
        return content

    new_content = re.sub(
        r'(<body[^>]*>)',
        r'\1\n' + BACK_LINK_SNIPPET,
        content,
        count=1,
        flags=re.IGNORECASE,
    )
    if new_content != content:
        print(f'  Injected back-link into {filename}')
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
    if new_content != content:
        print(f'  Injected og:image into {filename}')
    return new_content


def build_card(analysis: dict, index: int) -> str:
    color = ACCENT_COLORS[index % len(ACCENT_COLORS)]
    badges_html = ''.join(f'<span class="badge">{tag}</span>' for tag in analysis['tags'])
    desc_html = (
        f'<p class="card-desc">{analysis["description"]}</p>'
        if analysis['description'] else ''
    )
    date_html = (
        f'<span class="card-date">{analysis["date"]}</span>'
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
          <span class="card-link">View analysis →</span>
        </div>
      </a>'''




def build_html(analyses: list[dict]) -> str:
    count = len(analyses)
    subtitle = f'{count} analysis{"" if count == 1 else "es"}' if count else 'No analyses yet — drop an HTML file here'

    cards_html = '\n'.join(build_card(a, i) for i, a in enumerate(analyses))
    empty_html = (
        '<div class="empty">No analyses found yet.<br>Add <code>.html</code> files to the repo root and push.</div>'
        if not analyses else ''
    )

    og_image_url = f'{SITE_URL}/previews/index.png'
    og_desc = f'{count} analysis{"" if count == 1 else "es"} from various datasets and projects.' if count else 'A hub for data analysis visualizations and insights.'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DataDashboard</title>

  <!-- Open Graph / Social Sharing -->
  <meta property="og:type" content="website">
  <meta property="og:url" content="{SITE_URL}/">
  <meta property="og:title" content="DataDashboard">
  <meta property="og:description" content="{og_desc}">
  <meta property="og:image" content="{og_image_url}">
  <meta property="og:image:width" content="600">
  <meta property="og:image:height" content="315">

  <!-- Twitter -->
  <meta property="twitter:card" content="summary_large_image">
  <meta property="twitter:url" content="{SITE_URL}/">
  <meta property="twitter:title" content="DataDashboard">
  <meta property="twitter:description" content="{og_desc}">
  <meta property="twitter:image" content="{og_image_url}">

  <!-- RSS / Atom feed -->
  <link rel="alternate" type="application/atom+xml" title="DataDashboard feed" href="{SITE_URL}/feed.xml">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #f5f5f2;
      color: #222;
      min-height: 100vh;
    }}

    /* ── Header ─────────────────────────────────────────────── */
    header {{
      background: #1a1a2e;
      color: #fff;
      padding: 28px 32px 24px;
    }}
    header h1 {{
      font-size: 1.5rem;
      font-weight: 700;
      letter-spacing: -0.3px;
      margin-bottom: 4px;
    }}
    header h1 span {{
      color: #4f8ef7;
    }}
    .header-sub {{
      font-size: 0.82rem;
      color: rgba(255,255,255,0.45);
    }}

    /* ── Search ─────────────────────────────────────────────── */
    .search-bar {{
      padding: 16px 32px;
      background: #f5f5f2;
      border-bottom: 1px solid #e8e8e4;
    }}
    .search-bar input {{
      width: 100%;
      max-width: 480px;
      padding: 9px 14px;
      border-radius: 8px;
      border: 1px solid #d8d8d4;
      background: #fff;
      font-size: 0.85rem;
      color: #222;
      outline: none;
      transition: border-color 0.15s, box-shadow 0.15s;
    }}
    .search-bar input:focus {{
      border-color: #4f8ef7;
      box-shadow: 0 0 0 3px rgba(79,142,247,0.12);
    }}
    .search-bar input::placeholder {{ color: #aaa; }}

    /* ── Grid ───────────────────────────────────────────────── */
    main {{
      padding: 24px 32px 48px;
    }}
    .grid-label {{
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: #999;
      margin-bottom: 14px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 16px;
    }}

    /* ── Card ───────────────────────────────────────────────── */
    .card {{
      display: flex;
      flex-direction: column;
      background: #fff;
      border-radius: 12px;
      padding: 18px 18px 14px;
      box-shadow: 0 1px 6px rgba(0,0,0,0.07);
      border-top: 3px solid var(--accent, #4f8ef7);
      text-decoration: none;
      color: inherit;
      transition: transform 0.15s, box-shadow 0.15s;
      cursor: pointer;
    }}
    .card:hover {{
      transform: translateY(-2px);
      box-shadow: 0 4px 16px rgba(0,0,0,0.11);
    }}
    .card-top {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 8px;
    }}
    .card-title {{
      font-size: 0.92rem;
      font-weight: 700;
      color: #1a1a2e;
      line-height: 1.35;
      flex: 1;
    }}
    .badges {{
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      flex-shrink: 0;
      margin-top: 2px;
    }}
    .badge {{
      font-size: 0.62rem;
      font-weight: 700;
      letter-spacing: 0.04em;
      color: #4f8ef7;
      background: rgba(79,142,247,0.1);
      border-radius: 4px;
      padding: 2px 6px;
      white-space: nowrap;
    }}
    .card-desc {{
      font-size: 0.78rem;
      color: #666;
      line-height: 1.5;
      flex: 1;
      margin-bottom: 12px;
    }}
    .card-footer {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-top: auto;
      padding-top: 10px;
      border-top: 1px solid #f0f0ec;
    }}
    .card-date {{
      font-size: 0.72rem;
      color: #bbb;
      font-weight: 600;
    }}
    .card-link {{
      font-size: 0.75rem;
      font-weight: 700;
      color: var(--accent, #4f8ef7);
    }}

    /* ── Empty state ─────────────────────────────────────────── */
    .empty {{
      font-size: 0.88rem;
      color: #999;
      padding: 40px 0;
      text-align: center;
      line-height: 1.7;
    }}
    .empty code {{
      background: #eee;
      border-radius: 4px;
      padding: 1px 5px;
      font-size: 0.84em;
    }}

    /* ── Search match highlight ──────────────────────────────── */
    .card.hidden {{ display: none; }}
    .card.match {{ background: #fffdf5; box-shadow: 0 1px 6px rgba(0,0,0,0.07), 0 0 0 2px rgba(79,142,247,0.25); }}

    /* ── Keyboard focus ──────────────────────────────────────── */
    .card:focus-visible {{
      outline: 2px solid #4f8ef7;
      outline-offset: 2px;
    }}

    /* ── Footer ─────────────────────────────────────────────── */
    footer {{
      text-align: center;
      font-size: 0.7rem;
      color: #bbb;
      padding: 0 32px 28px;
    }}

    /* ── Responsive ──────────────────────────────────────────── */
    @media (max-width: 600px) {{
      header {{ padding: 20px 18px 18px; }}
      .search-bar {{ padding: 12px 18px; }}
      main {{ padding: 18px 18px 40px; }}
      footer {{ padding: 0 18px 24px; }}
    }}
  </style>
</head>
<body>

<header>
  <h1>Data<span>Dashboard</span></h1>
  <div class="header-sub">{subtitle}</div>
</header>

<div class="search-bar">
  <input id="search" type="search" placeholder="Search analyses…" autocomplete="off">
</div>

<main>
  <div class="grid-label">Analyses</div>
  <div class="grid" id="grid">
{cards_html}
  </div>
  {empty_html}
</main>

<footer>
  Auto-generated · <a href="https://github.com/Teakayah/dashboard" style="color:#bbb" target="_blank" rel="noopener noreferrer">Teakayah/dashboard</a>
  &nbsp;·&nbsp;
  <a href="{SITE_URL}/feed.xml" style="color:#bbb" title="Subscribe via RSS/Atom">&#x2605; RSS feed</a>
</footer>

<script>
  const input = document.getElementById('search');
  const cards = document.querySelectorAll('.card');
  input.addEventListener('input', () => {{
    const q = input.value.trim().toLowerCase();
    cards.forEach(c => {{
      const text = c.textContent.toLowerCase();
      const matches = q !== '' && text.includes(q);
      c.classList.toggle('hidden', q !== '' && !matches);
      c.classList.toggle('match', matches);
    }});
  }});
</script>

</body>
</html>
'''


def main(argv: list[str] | None = None):
    args = parse_args(argv)
    analyses = get_analyses()

    # Inject enhancements into each analysis page
    for a in analyses:
        filepath = ROOT / a['filename']
        try:
            content = filepath.read_text(encoding='utf-8')
        except Exception:
            continue

        new_content = inject_responsive(content, a['filename'], args.responsive_preset)
        new_content = inject_back_link(new_content, a['filename'])
        new_content = inject_og_tags(new_content, a['filename'], filepath.stem)

        if new_content != content:
            filepath.write_text(new_content, encoding='utf-8')

    html = build_html(analyses)
    output = ROOT / 'index.html'
    output.write_text(html, encoding='utf-8')
    print(f'Generated index.html with {len(analyses)} analysis file(s).')
    for a in analyses:
        print(f'  - {a["filename"]} → {a["title"]}')


if __name__ == '__main__':
    main()
