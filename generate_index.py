#!/usr/bin/env python3
"""
Generate index.html from all HTML analysis files in the repository root.
Run locally or via GitHub Actions on every push.
"""

import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent
EXCLUDE = {'index.html', 'generate_index.py'}

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


def extract_meta(filepath: Path) -> dict:
    """Extract title, description, and tags from an HTML file."""
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

    # Detect Chart.js usage
    uses_chartjs = bool(re.search(r'chart\.js|chart\.umd', content, re.IGNORECASE))

    # File modification time
    mtime = filepath.stat().st_mtime
    date_str = datetime.fromtimestamp(mtime).strftime('%b %Y')

    return {
        'filename': filepath.name,
        'title': title,
        'description': description,
        'uses_chartjs': uses_chartjs,
        'date': date_str,
    }


def _fallback(filepath: Path) -> dict:
    return {
        'filename': filepath.name,
        'title': filepath.stem.replace('_', ' ').title(),
        'description': '',
        'uses_chartjs': False,
        'date': '',
    }


def get_analyses() -> list[dict]:
    analyses = []
    for html_file in sorted(ROOT.glob('*.html'), key=lambda p: p.stat().st_mtime, reverse=True):
        if html_file.name.lower() in EXCLUDE:
            continue
        analyses.append(extract_meta(html_file))
    return analyses


def build_card(analysis: dict, index: int) -> str:
    color = ACCENT_COLORS[index % len(ACCENT_COLORS)]
    chartjs_badge = (
        '<span class="badge">Chart.js</span>' if analysis['uses_chartjs'] else ''
    )
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
          {chartjs_badge}
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

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DataDashboard</title>
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
    .badge {{
      flex-shrink: 0;
      font-size: 0.62rem;
      font-weight: 700;
      letter-spacing: 0.04em;
      color: #4f8ef7;
      background: rgba(79,142,247,0.1);
      border-radius: 4px;
      padding: 2px 6px;
      white-space: nowrap;
      margin-top: 2px;
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

    /* ── Hide on search ──────────────────────────────────────── */
    .card.hidden {{ display: none; }}

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
  Auto-generated · <a href="https://github.com/Teakayah/dashboard" style="color:#bbb">Teakayah/dashboard</a>
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

</body>
</html>
'''


def main():
    analyses = get_analyses()
    html = build_html(analyses)
    output = ROOT / 'index.html'
    output.write_text(html, encoding='utf-8')
    print(f'Generated index.html with {len(analyses)} analysis file(s).')
    for a in analyses:
        print(f'  - {a["filename"]} → {a["title"]}')


if __name__ == '__main__':
    main()
