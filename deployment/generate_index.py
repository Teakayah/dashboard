#!/usr/bin/env python3
"""
Generate index.html from all HTML analysis files in the repository root.
Run locally or in CI to rebuild the dashboard.
"""

import os
import re
import json
import random
from datetime import datetime
from pathlib import Path
import html

# --- Configuration ---
ROOT = Path(".")
EXCLUDE = {"index.html", "dropzone.html", "404.html", "template.html", "Readme.md"}
SITE_URL = "https://teakayah.github.io/dashboard"
ACCENT_COLORS = ["#4f8ef7", "#2ecc71", "#f39c12", "#e74c3c", "#9b59b6", "#1abc9c"]

# --- Metadata Extraction ---

def get_metadata(file_path: Path) -> dict:
    """Extract metadata from an HTML file by looking for specific markers or tags."""
    content = file_path.read_text(encoding='utf-8')
    
    # 1. Try to find a title
    title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else file_path.stem.replace('_', ' ').title()
    title = title.replace('&amp;', '&').replace('"', '&quot;')

    # 2. Look for a date (StatCan specific format usually)
    date_match = re.search(r'Last updated: ([\d-]+)', content)
    date = date_match.group(1) if date_match else ""
    if not date:
        # Fallback to file mtime if no date found
        mtime = os.path.getmtime(file_path)
        date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')

    # 3. Look for tags in a custom meta tag or comment
    tags = []
    tags_match = re.search(r'<meta name="keywords" content="(.*?)"', content)
    if tags_match:
        tags = [t.strip() for t in tags_match.group(1).split(',')]
    else:
        # Heuristic tags based on filename
        if 'flood' in file_path.name: tags.append('Environment')
        if 'employment' in file_path.name: tags.append('Economy')
        if 'price' in file_path.name: tags.append('Real Estate')

    # 4. Description
    desc_match = re.search(r'<meta name="description" content="(.*?)"', content)
    description = desc_match.group(1) if desc_match else ""

    return {
        "filename": file_path.name,
        "stem": file_path.stem,
        "title": title,
        "date": date,
        "tags": tags[:3], # Limit to 3 tags
        "description": description
    }

# --- HTML Injection (for individual analysis pages) ---

def inject_responsive(content: str, filename: str, preset_name: str = 'default') -> str:
    """Inject responsive viewport and basic CSS into an analysis HTML file if not present."""
    if preset_name == 'none':
        return content

    if 'responsive-inject-v' in content:
        # Check version
        if 'responsive-inject-v5' in content:
            return content
        else:
            # Strip old version (optionally handles missing closing tag)
            content = re.sub(r'<!-- responsive-inject-v\d+ -->.*?<!-- /responsive-inject-v\d+ -->', '', content, flags=re.DOTALL)
            content = re.sub(r'<!-- responsive-inject-v\d+ -->', '', content)

    v5_style = """
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
  <!-- /responsive-inject-v5 -->"""

    # Insert just after <head>
    new_content = re.sub(r'(<head[^>]*>)', r'\1' + v5_style, content, count=1, flags=re.IGNORECASE)
    return new_content

def inject_assets(content: str, filename: str) -> str:
    """Inject theme.css and fullscreen.js if missing."""
    assets = ""
    if 'theme.css' not in content:
        assets += '\n  <link rel="stylesheet" href="assets/theme.css">'
    if 'fullscreen.js' not in content:
        assets += '\n  <script src="assets/fullscreen.js"></script>'
    
    if not assets:
        return content

    # Insert just before </head>
    new_content = re.sub(r'(</head>)', assets + r'\n\1', content, count=1, flags=re.IGNORECASE)
    return new_content


HEADER_MARKER = '<!-- unified-header-inject -->'

def build_header(current_filename: str) -> str:
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
    if HEADER_MARKER in content:
        return content
    
    header_html = build_header(filename)
    # Insert at the start of <body>
    new_content = re.sub(r'(<body[^>]*>)', r'\1\n' + header_html, content, count=1, flags=re.IGNORECASE)
    return new_content


def inject_og_tags(content: str, filename: str, stem: str) -> str:
    """Inject og:image/twitter:image into an analysis HTML file content if not already present."""
    if 'og:image' in content:
        return content  # already has one, leave it alone

    image_url = f'{SITE_URL}/previews/{html.escape(stem, quote=True)}.png'
    esc_filename = html.escape(filename, quote=True)

    # Extract title for og:title
    title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else stem.replace('_', ' ').title()
    title = title.replace('&amp;', '&').replace('"', '&quot;')

    og_block = (
        f'\n  <!-- Open Graph / Social Sharing -->'
        f'\n  <meta property="og:type" content="article">'
        f'\n  <meta property="og:url" content="{SITE_URL}/{esc_filename}">'
        f'\n  <meta property="og:title" content="{title}">'
        f'\n  <meta property="og:image" content="{html.escape(image_url, quote=True)}">'
        f'\n  <meta property="og:image:width" content="600">'
        f'\n  <meta property="og:image:height" content="315">'
        f'\n  <meta property="twitter:card" content="summary_large_image">'
        f'\n  <meta property="twitter:image" content="{html.escape(image_url, quote=True)}">'
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
        f'<a href="{html.escape(m["filename"], quote=True)}" class="related-link"><strong>{html.escape(m["title"], quote=True)}</strong><span>{html.escape(m["date"], quote=True)}</span></a>'
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
    badges_html = ''.join(f'<span class="badge">{html.escape(tag, quote=True)}</span>' for tag in analysis['tags'])
    desc_html = (
        f'<p class="card-desc">{html.escape(analysis["description"], quote=True)}</p>'
        if analysis['description'] else ''
    )
    date_html = (
        f'<div class="card-date">Last Updated: <span>{html.escape(analysis["date"], quote=True)}</span></div>'
        if analysis['date'] else ''
    )
    return f'''      <a class="card" href="{html.escape(analysis['filename'], quote=True)}" style="--accent:{color}">
        <div class="card-top">
          <div class="card-title">{html.escape(analysis['title'], quote=True)}</div>
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
    .grid-label::after {{ content: ""; flex: 1; height: 1px; background: var(--border); }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 32px; }}
    
    .card {{ 
      background: var(--card-bg); 
      border: 1px solid var(--border); 
      border-radius: 16px; 
      padding: 24px; 
      text-decoration: none; 
      color: inherit; 
      display: flex; 
      flex-direction: column; 
      transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
      box-shadow: var(--shadow);
    }}
    .card:hover {{ transform: translateY(-4px); border-color: var(--accent); box-shadow: 0 12px 24px rgba(0,0,0,0.06); }}
    .card.hidden {{ display: none; }}
    
    .card-top {{ margin-bottom: 16px; }}
    .card-title {{ font-size: 1.15rem; font-weight: 700; color: var(--text); line-height: 1.3; margin-bottom: 8px; }}
    .badges {{ display: flex; flex-wrap: wrap; gap: 6px; }}
    .badge {{ font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; padding: 4px 10px; border-radius: 20px; background: rgba(0,0,0,0.05); color: var(--text-muted); }}
    
    .card-desc {{ font-size: 0.85rem; color: var(--text-muted); line-height: 1.5; margin-bottom: 24px; flex: 1; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }}
    
    .card-footer {{ display: flex; align-items: center; justify-content: space-between; border-top: 1px solid var(--border); pt: 16px; margin-top: auto; padding-top: 16px; }}
    .card-date {{ font-size: 0.72rem; color: var(--text-dim); }}
    .card-date span {{ font-weight: 600; color: var(--text-muted); }}
    .card-link {{ font-size: 0.8rem; font-weight: 700; color: var(--primary); }}

    .empty {{ text-align: center; padding: 80px 0; color: var(--text-dim); }}
    
    footer {{ text-align: center; padding: 48px; color: var(--text-dim); font-size: 0.8rem; border-top: 1px solid var(--border); margin-top: 64px; }}

    @media (max-width: 640px) {{
      header.hero {{ padding: 48px 24px 40px; }}
      header.hero h1 {{ font-size: 1.8rem; }}
      main {{ padding: 32px 20px; }}
      .grid {{ grid-template-columns: 1fr; gap: 20px; }}
    }}
  </style>
</head>
<body>
  <header class="hero">
    <h1>Data<span>Dashboard</span></h1>
    <p class="header-sub">{subtitle}</p>
  </header>

  <div class="search-bar">
    <input type="text" id="search" placeholder="Search analyses, tags, or dates..." autocomplete="off">
  </div>

  <main>
    <div class="grid-label">Available Analyses</div>
    <div class="grid">
      {cards_html}
    </div>
    {empty_html}
  </main>

  <footer>
    &copy; {datetime.now().year} DataDashboard &middot; Built with Python &amp; DuckDB
  </footer>
<script>
  const input = document.getElementById('search');
  const cards = document.querySelectorAll('.card');

  function highlight(text, query) {{
    if (!query) return text;
    const regex = new RegExp(`(${{query}})`, 'gi');
    return text.replace(regex, '<mark style="background: #ffeb3b; padding: 0 2px; border-radius: 2px; color: #000;">$1</mark>');
  }}

  input.addEventListener('input', () => {{
    const q = input.value.trim().toLowerCase();
    cards.forEach(c => {{
      const titleEl = c.querySelector('.card-title');
      const descEl = c.querySelector('.card-desc');

      if (!c.dataset.origTitle) c.dataset.origTitle = titleEl.innerHTML;
      if (descEl && !c.dataset.origDesc) c.dataset.origDesc = descEl.innerHTML;

      const text = c.textContent.toLowerCase();
      const matches = q === '' || text.includes(q);
      c.classList.toggle('hidden', !matches);

      if (q !== '' && matches) {{
        titleEl.innerHTML = highlight(c.dataset.origTitle, q);
        if (descEl) descEl.innerHTML = highlight(c.dataset.origDesc, q);
      }} else {{
        titleEl.innerHTML = c.dataset.origTitle || titleEl.innerHTML;
        if (descEl) descEl.innerHTML = c.dataset.origDesc || (descEl ? descEl.innerHTML : '');
      }}
    }});
  }});
</script>
<script>
  if ('serviceWorker' in navigator) {{
    window.addEventListener('load', () => {{
      navigator.serviceWorker.register('/sw.js').then(reg => {{
        console.log('SW registered:', reg);
      }}).catch(err => {{
        console.log('SW registration failed:', err);
      }});
    }});
  }}
</script>
</body>
</html>'''

def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--responsive-preset', default='default')
    args = parser.parse_args(argv)

    print("Generating index.html and updating analyses...")
    
    html_files = [f for f in ROOT.glob("*.html") if f.name not in EXCLUDE]
    all_meta = []

    for f in html_files:
        print(f"  Processing {f.name}...")
        meta = get_metadata(f)
        all_meta.append(meta)

        # Inject components into analysis pages
        content = f.read_text(encoding='utf-8')
        content = inject_responsive(content, f.name, args.responsive_preset)
        content = inject_assets(content, f.name)
        content = inject_unified_header(content, f.name)
        content = inject_og_tags(content, f.name, meta['stem'])
        content = inject_pwa_script(content)
        # Note: inject_related_links needs all_meta, so we do it in a second pass
        f.write_text(content, encoding='utf-8')

    # Second pass for cross-analysis injections
    for f in html_files:
        content = f.read_text(encoding='utf-8')
        content = inject_related_links(content, f.name, all_meta)
        f.write_text(content, encoding='utf-8')

    # Build and write index.html
    # Sort by date descending
    all_meta.sort(key=lambda x: x['date'], reverse=True)
    index_content = build_html(all_meta)
    (ROOT / "index.html").write_text(index_content, encoding='utf-8')
    print(f"Generated index.html with {len(all_meta)} analyses.")

if __name__ == "__main__":
    main()
