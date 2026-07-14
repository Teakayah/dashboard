#!/usr/bin/env python3
"""
Generate index.html from all HTML analysis files in the repository root.
Run locally or via GitHub Actions on every push.
"""

import argparse
import html
import json
import re
from pathlib import Path
from typing import Optional

from .git_utils import get_git_dates_batched

# Import centralized configuration
try:
    from config import ROOT, SITE_URL, LIBRARY_PATTERNS, ACCENT_COLORS
except ImportError:
    from deployment.config import ROOT, SITE_URL, LIBRARY_PATTERNS, ACCENT_COLORS

EXCLUDE = {'index.html'}

DESCRIPTIONS_FILE = ROOT / 'descriptions.json'


def load_descriptions() -> dict:
    """Load pre-generated AI descriptions from descriptions.json (committed to repo)."""
    if DESCRIPTIONS_FILE.exists():
        return json.loads(DESCRIPTIONS_FILE.read_text(encoding='utf-8'))
    return {}


def extract_meta(filepath: Path, content: str, descriptions: Optional[dict] = None, git_date: Optional[str] = None) -> dict:
    """Extract title, description, and tags from an HTML file content.

    Falls back to pre-generated descriptions from descriptions.json when no
    <meta name="description"> or subtitle element is found in the HTML.
    """
    # Title
    title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else filepath.stem.replace('_', ' ').title()
    # Clean HTML entities in title
    title = html.unescape(title)

    # Meta description
    desc_match = re.search(
        r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']',
        content, re.IGNORECASE
    )
    description = desc_match.group(1).strip() if desc_match else ''

    # If no meta description, look for a subtitle element (common pattern in your files)
    if not description:
        # Regex breakdown:
        # <([a-zA-Z0-9]+)   - Group 1: Captures the HTML tag name (e.g., div, span, p)
        # [^>]*class=...    - Ensures the tag has a class attribute containing 'subtitle'
        # >(.*?)</\1>       - Group 2: Non-greedily captures the inner content.
        #                     The \1 backreference dynamically matches the exact closing tag
        #                     captured in Group 1, preventing premature matches if inner tags exist.
        sub_match = re.search(r'<([a-zA-Z0-9]+)[^>]*class=["\'][^"\']*subtitle[^"\']*["\'][^>]*>(.*?)</\1>', content, re.IGNORECASE | re.DOTALL)
        if sub_match:
            description = re.sub(r'<[^>]+>', '', sub_match.group(2)).strip()
            description = re.sub(r'\s+', ' ', description)
            if len(description) > 120:
                description = description[:117] + '…'

    # Fallback: use pre-generated description from descriptions.json
    if not description and descriptions:
        description = descriptions.get(filepath.name, '')

    description = html.unescape(description)

    # Detect visualization libraries
    tags = [name for name, pattern in LIBRARY_PATTERNS.items()
            if re.search(pattern, content, re.IGNORECASE)]

    return {
        'filename': filepath.name,
        'title': title,
        'description': description,
        'tags': tags,
        'date': git_date or '',
    }


def _fallback(filepath: Path, date_str: str = "") -> dict:
    return {
        'filename': filepath.name,
        'title': filepath.stem.replace('_', ' ').title(),
        'description': '',
        'tags': [],
        'date': date_str,
    }


RESPONSIVE_PRESETS = {
    'default': {
        'marker': '<!-- responsive-inject-v7 -->',
        'snippet': '''\
  <!-- responsive-inject-v7 -->
  <style>
    @media (min-width: 769px) {
      .dashboard-container { display: flex; flex-direction: row; }
      .sidebar { width: 300px; flex-shrink: 0; }
      .main-content { flex-grow: 1; }
    }
  </style>
  <!-- /responsive-inject-v7 -->''',
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
    """Inject responsive desktop layout enhancer into an analysis HTML file content.

    Injected right after <head> so the Chart.js defineProperty trap runs
    before chart.js itself is loaded (which typically appears in <head>).
    Strips any older version of the injection before re-injecting.
    Files that already contain the current marker are left untouched so that
    hand-crafted responsive blocks are not overwritten by the default preset.
    """
    preset = RESPONSIVE_PRESETS[preset_name]

    # Matches and extracts previous responsive injection blocks to safely strip them.
    strip_regex = re.compile(
        r'''
        \s*                                     # Match any leading whitespace
        <!--\ responsive-inject(?:-v\d+)?\ -->  # Opening marker with optional version (e.g. -v5)
        \s*<style>.*?</style>                   # Match the injected CSS block non-greedily
        \s*<script>.*?</script>                 # Match the injected JavaScript block non-greedily
        (?:                                     # Optional non-capturing group for the closing marker
            \s*<!--\ /responsive-inject(?:-v\d+)?\ -->
        )?
        ''',
        flags=re.DOTALL | re.VERBOSE,
    )

    if preset_name == 'none':
        new_content = strip_regex.sub('', content)
        if new_content != content:
            print(f'  Removed responsive enhancer from {filename}')
        return new_content

    marker = preset['marker']
    snippet = preset['snippet']

    # If the current marker is already present, the file has a hand-crafted or
    # up-to-date block — leave it completely untouched.
    if marker in content:
        return content

    # Strip any older-version block, then inject the current preset.
    new_content = strip_regex.sub('', content)
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


def strip_back_link(content: str, filename: str) -> str:
    """Remove the legacy arrow back-link div; the unified header is the canonical nav."""
    if BACK_LINK_MARKER not in content:
        return content
    new_content = re.sub(
        r'\n?<!-- back-link-inject -->(?:<div[^>]*>.*?</div>)?',
        '',
        content,
        count=1,
        flags=re.DOTALL,
    )
    if new_content != content:
        print(f'  Stripped legacy back-link from {filename}')
    return new_content



def inject_favicon(content: str, filename: str) -> str:
    """Inject favicon link into an analysis HTML file content if not already present."""
    if 'rel="icon"' in content or "rel='icon'" in content:
        return content  # already has one, leave it alone

    favicon_link = f'\n  <link rel="icon" href="{SITE_URL}/favicon.ico" type="image/x-icon">'

    # Insert just before </head>
    new_content = re.sub(r'(</head>)', favicon_link + r'\n\1', content, count=1, flags=re.IGNORECASE)
    if new_content != content:
        print(f'  Injected favicon into {filename}')
    return new_content


def inject_csp(content: str, filename: str) -> str:
    """Inject a Content Security Policy meta tag into an analysis HTML file."""
    if 'Content-Security-Policy' in content:
        return content

    csp_block = (
        '\n  <meta http-equiv="Content-Security-Policy" content="default-src \'self\'; '
        'script-src \'self\' \'unsafe-inline\' \'unsafe-eval\' https://cdn.jsdelivr.net; '
        'style-src \'self\' \'unsafe-inline\' https://fonts.googleapis.com; '
        'font-src \'self\' https://fonts.gstatic.com; '
        'img-src \'self\' data: https:; '
        'connect-src \'self\' https: blob:; '
        'worker-src \'self\' blob:">'
    )

    new_content = re.sub(r'(<head[^>]*>)', r'\1' + csp_block, content, count=1, flags=re.IGNORECASE)
    if new_content != content:
        print(f'  Injected CSP into {filename}')
    return new_content


def inject_og_tags(content: str, filename: str, stem: str) -> str:
    """Inject og:image/twitter:image into an analysis HTML file content if not already present."""
    if 'og:image' in content:
        return content  # already has one, leave it alone

    image_url = f'{SITE_URL}/previews/{stem}.png'

    # Extract title for og:title
    title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else stem.replace('_', ' ').title()
    title = html.escape(html.unescape(title), quote=True)

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
    badges_html = ''.join(f'<span class="badge">{html.escape(tag)}</span>' for tag in analysis['tags'])
    desc_html = (
        f'<p class="card-desc">{html.escape(analysis["description"])}</p>'
        if analysis['description'] else ''
    )
    date_html = (
        f'<span class="card-date">{html.escape(analysis["date"])}</span>'
        if analysis['date'] else ''
    )
    return f'''      <a class="card" href="{html.escape(analysis['filename'], quote=True)}" style="--accent:{color}">
        <div class="card-top">
          <div class="card-title">{html.escape(analysis['title'])}</div>
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
    subtitle = f'{count} analys{"is" if count == 1 else "es"}' if count else 'No analyses yet — drop an HTML file here'

    cards_html = '\n'.join(build_card(a, i) for i, a in enumerate(analyses))
    empty_html = (
        '<div class="empty">No analyses found yet.<br>Add <code>.html</code> files to the repo root and push.</div>'
        if not analyses else ''
    )

    og_image_url = f'{SITE_URL}/previews/index.png'
    og_desc = f'{count} analys{"is" if count == 1 else "es"} from various datasets and projects.' if count else 'A hub for data analysis visualizations and insights.'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DataDashboard</title>
  <link rel="icon" href="{SITE_URL}/favicon.ico" type="image/x-icon">

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
      color: #60a5fa;
    }}
    .header-sub {{
      font-size: 0.82rem;
      color: rgba(255,255,255,0.85);
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
      border-color: #1e40af;
      box-shadow: 0 0 0 3px rgba(79,142,247,0.12);
    }}
    .search-bar input::placeholder {{ color: #6b7280; }}

    /* ── Grid ───────────────────────────────────────────────── */
    main {{
      padding: 24px 32px 48px;
    }}
    .grid-label {{
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: #4b5563;
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
      border-top: 3px solid var(--accent, #1d4ed8);
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
      color: #1e40af;
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
      color: #4b5563;
      font-weight: 600;
    }}
    .card-link {{
      font-size: 0.75rem;
      font-weight: 700;
      color: var(--accent, #2563eb);
    }}

    /* ── Empty state ─────────────────────────────────────────── */
    .empty {{
      font-size: 0.88rem;
      color: #4b5563;
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
    button:focus-visible {{
      outline: 2px solid #1d4ed8;
      outline-offset: 2px;
    }}
    .card:focus-visible {{
      outline: 2px solid #1d4ed8;
      outline-offset: 2px;
    }}

    /* ── Footer ─────────────────────────────────────────────── */
    footer {{
      text-align: center;
      font-size: 0.7rem;
      color: #4b5563;
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

<search><div class="search-bar">
  <input id="search" type="search" placeholder="Search analyses…" autocomplete="off" aria-label="Search analyses">
</div></search>

<main>
  <div class="grid-label">Analyses</div>
  <div class="grid" id="grid">
{cards_html}
  </div>
  {empty_html}
  <div id="no-results" class="empty hidden">No analyses found matching "<strong></strong>".</div>
</main>

<footer>
  Auto-generated · <a href="https://github.com/Teakayah/dashboard" style="color:#4b5563" target="_blank" rel="noopener noreferrer">Teakayah/dashboard</a>
  &nbsp;·&nbsp;
  <a href="{SITE_URL}/feed.xml" style="color:#4b5563" title="Subscribe via RSS/Atom">&#x2605; RSS feed</a>
</footer>

<script>
  const input = document.getElementById('search');
  const cards = document.querySelectorAll('.card');
  const noResults = document.getElementById('no-results');
  const noResultsQuery = noResults.querySelector('strong');

  function debounce(func, wait) {{
    let timeout;
    return function(...args) {{
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(this, args), wait);
    }};
  }}

  input.addEventListener('input', debounce(() => {{
    const q = input.value.trim().toLowerCase();
    let visibleCount = 0;

    cards.forEach(c => {{
      const text = c.textContent.toLowerCase();
      const matches = q !== '' && text.includes(q);
      const isHidden = q !== '' && !matches;
      c.classList.toggle('hidden', isHidden);
      c.classList.toggle('match', matches);

      if (!isHidden) {{
        visibleCount++;
      }}
    }});

    if (visibleCount === 0 && q !== '') {{
      noResultsQuery.textContent = input.value;
      noResults.classList.remove('hidden');
    }} else {{
      noResults.classList.add('hidden');
    }}
  }}, 250));
</script>

</body>
</html>
'''


CONTRAST_FIX_MARKER = 'data-contrast-fix'

CONTRAST_FIX_STYLE = (
    '\n  <style data-contrast-fix>'
    'body{background:var(--bg)!important;color:var(--text)!important}'
    'h1,h2,h3,h4,h5,h6{color:var(--text)!important}'
    'a{color:var(--primary,#2563eb)}'
    '.subtitle,.note,.empty,.tab:not(.active),.related-label,.card-date'
    '{color:var(--text-muted,#4b5563)!important}'
    '.related-link span,footer,footer a{color:var(--text-muted,#4b5563)!important}'
    'button.tab{background:transparent;border:none;border-bottom:3px solid transparent;font-family:inherit;outline:none}button.tab.active{border-bottom-color:var(--primary,#1a1a2e)}button.tab:focus-visible{outline:2px solid var(--primary,#1a1a2e);outline-offset:-2px}'
    '</style>'
)


def inject_contrast_fix(content: str, filename: str) -> str:
    """Inject a CSS override that fixes dark-mode body colours and WCAG AA contrast failures."""
    if CONTRAST_FIX_MARKER in content:
        return content
    new_content = re.sub(r'(</head>)', CONTRAST_FIX_STYLE + r'\n\1', content, count=1, flags=re.IGNORECASE)
    if new_content != content:
        print(f'  Injected contrast fix into {filename}')
    return new_content


def strip_analysis_utils(content: str, filename: str) -> str:
    """Remove any leftover <script src="assets/analysis_utils.js"> tags (idempotent)."""
    import re as _re
    pattern = r'<script[^>]+src=["\']assets/analysis_utils\.js["\'][^>]*>\s*</script>'
    new_content = _re.sub(pattern, '', content, flags=_re.IGNORECASE)
    if new_content != content:
        print(f'  Stripped analysis_utils.js script tag from {filename}')
    return new_content


def inject_share_fix(content: str, filename: str) -> str:
    """Replace bare navigator.share onclick with a feature-detected version."""
    unsafe = 'onclick="navigator.share({title: document.title, url: window.location.href})"'
    safe = ('onclick="if(navigator.share){navigator.share({title:document.title,'
            'url:window.location.href})}else if(navigator.clipboard)'
            '{navigator.clipboard.writeText(window.location.href)}"')
    if unsafe not in content:
        return content
    new_content = content.replace(unsafe, safe)
    if new_content != content:
        print(f'  Fixed navigator.share in {filename}')
    return new_content


def main(argv: Optional[list[str]] = None):
    args = parse_args(argv)
    descriptions = load_descriptions()
    analyses = []

    # Process all HTML files, extract meta, and inject enhancements
    html_files = [p for p in ROOT.glob('*.html') if p.name.lower() not in EXCLUDE]
    # Sort files by modification time before we potentially write back and alter their mtime
    html_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    # Batch git date retrieval for all HTML files
    git_dates = get_git_dates_batched(html_files)

    for filepath in html_files:
        date_str = git_dates.get(filepath, "")
        try:
            content = filepath.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            # Fallback for file read errors if any
            analyses.append(_fallback(filepath, date_str))
            continue

        # Extract meta
        meta = extract_meta(filepath, content, descriptions=descriptions, git_date=date_str)
        analyses.append(meta)

        # Inject enhancements
        new_content = inject_responsive(content, meta['filename'], args.responsive_preset)
        new_content = strip_back_link(new_content, meta['filename'])
        new_content = strip_analysis_utils(new_content, meta['filename'])
        new_content = inject_favicon(new_content, meta['filename'])
        new_content = inject_og_tags(new_content, meta['filename'], filepath.stem)
        new_content = inject_share_fix(new_content, meta['filename'])
        new_content = inject_contrast_fix(new_content, meta['filename'])
        new_content = inject_csp(new_content, meta['filename'])

        if new_content != content:
            filepath.write_text(new_content, encoding='utf-8')

    html = build_html(analyses)
    output = ROOT / 'index.html'
    output.write_text(html, encoding='utf-8')
    print(f'Generated index.html with {len(analyses)} analysis file(s).')
    for a in analyses:
        print(f'  - {a["filename"]} → {a["title"]}')


if __name__ == '__main__':  # pragma: no cover
    main()
