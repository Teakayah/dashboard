#!/usr/bin/env python3
"""
Generate index.html from all HTML analysis files in the repository root.
Run locally or via GitHub Actions on every push.
"""

import argparse
import html
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent.parent
EXCLUDE = {"index.html"}
SITE_URL = "https://teakayah.github.io/dashboard"

# Visualization library detection patterns for card badges
LIBRARY_PATTERNS = {
    "Chart.js": r"chart\.js|chart\.umd",
    "D3.js": r"d3(?:\.v\d+)?(?:\.min)?\.js|cdn\.jsdelivr\.net/npm/d3@",
    "Plotly": r"plotly(?:\.min)?\.js|cdn\.plot\.ly",
    "Vega": r"vega(?:-lite)?(?:\.min)?\.js",
    "DuckDB": r"duckdb",
    "Grid.js": r"gridjs",
}

# Chart.js-inspired accent colors (top border on cards)
ACCENT_COLORS = [
    "#4f8ef7",  # blue
    "#ff6384",  # pink/red
    "#4bc0c0",  # teal
    "#ff9f40",  # orange
    "#9966ff",  # purple
    "#36a2eb",  # sky blue
    "#ffce56",  # yellow
    "#2ecc71",  # green
]


DESCRIPTIONS_FILE = ROOT / "descriptions.json"


def load_descriptions() -> dict:
    """Load pre-generated AI descriptions from descriptions.json (committed to repo)."""
    if DESCRIPTIONS_FILE.exists():
        return json.loads(DESCRIPTIONS_FILE.read_text(encoding="utf-8"))
    return {}


def _git_date(filepath: Path) -> str:
    """Return 'Mon YYYY' from git log; fall back to mtime if the file isn't committed."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ci", "--", str(filepath)],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        stamp = result.stdout.strip()
        if stamp:
            return datetime.fromisoformat(stamp).strftime("%b %Y")
    except Exception:
        pass
    return datetime.fromtimestamp(filepath.stat().st_mtime).strftime("%b %Y")


def extract_meta(
    filepath: Path, content: str, descriptions: Optional[dict] = None
) -> dict:
    """Extract title, description, and tags from an HTML file content.

    Falls back to pre-generated descriptions from descriptions.json when no
    <meta name="description"> or subtitle element is found in the HTML.
    """
    # Title
    title_match = re.search(
        r"<title[^>]*>(.*?)</title>", content, re.IGNORECASE | re.DOTALL
    )
    title = (
        title_match.group(1).strip()
        if title_match
        else filepath.stem.replace("_", " ").title()
    )
    # Clean HTML entities in title
    title = html.unescape(title)

    # Meta description
    desc_match = re.search(
        r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']',
        content,
        re.IGNORECASE,
    )
    description = desc_match.group(1).strip() if desc_match else ""

    # If no meta description, look for a subtitle element (common pattern in your files)
    if not description:
        sub_match = re.search(
            r'class=["\'][^"\']*subtitle[^"\']*["\'][^>]*>(.*?)</[a-z]+>',
            content,
            re.IGNORECASE | re.DOTALL,
        )
        if sub_match:
            description = re.sub(r"<[^>]+>", "", sub_match.group(1)).strip()
            description = re.sub(r"\s+", " ", description)
            if len(description) > 120:
                description = description[:117] + "…"

    # Fallback: use pre-generated description from descriptions.json
    if not description and descriptions:
        description = descriptions.get(filepath.name, "")

    description = html.unescape(description)

    # Detect visualization libraries
    tags = [
        name
        for name, pattern in LIBRARY_PATTERNS.items()
        if re.search(pattern, content, re.IGNORECASE)
    ]

    # Date from git log (CI-safe; mtime is always "now" after checkout)
    date_str = _git_date(filepath)

    return {
        "filename": filepath.name,
        "title": title,
        "description": description,
        "tags": tags,
        "date": date_str,
    }


def _fallback(filepath: Path) -> dict:
    return {
        "filename": filepath.name,
        "title": filepath.stem.replace("_", " ").title(),
        "description": "",
        "tags": [],
        "date": "",
    }


RESPONSIVE_PRESETS = {
    "default": {
        "marker": "<!-- responsive-inject-v5 -->",
        "snippet": """\
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
  <!-- /responsive-inject-v5 -->""",
    },
    "none": {
        "marker": None,
        "snippet": None,
    },
}


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.strip())
    parser.add_argument(
        "--responsive-preset",
        choices=sorted(RESPONSIVE_PRESETS),
        default="default",
        help="Responsive injection preset to apply to analysis pages.",
    )
    return parser.parse_args(argv)


def inject_responsive(content: str, filename: str, preset_name: str = "default") -> str:
    """Inject responsive desktop layout enhancer into an analysis HTML file content.

    Injected right after <head> so the Chart.js defineProperty trap runs
    before chart.js itself is loaded (which typically appears in <head>).
    Strips any older version of the injection before re-injecting.
    Files that already contain the current marker are left untouched so that
    hand-crafted responsive blocks are not overwritten by the default preset.
    """
    preset = RESPONSIVE_PRESETS[preset_name]

    if preset_name == "none":
        new_content = re.sub(
            r"\s*<!-- responsive-inject(?:-v\d+)? -->\s*<style>.*?</style>\s*<script>.*?</script>(?:\s*<!-- /responsive-inject(?:-v\d+)? -->)?",
            "",
            content,
            flags=re.DOTALL,
        )
        if new_content != content:
            print(f"  Removed responsive enhancer from {filename}")
        return new_content

    marker = preset["marker"]
    snippet = preset["snippet"]

    # If the current marker is already present, the file has a hand-crafted or
    # up-to-date block — leave it completely untouched.
    if marker in content:
        return content

    # Strip any older-version block, then inject the current preset.
    new_content = re.sub(
        r"\s*<!-- responsive-inject(?:-v\d+)? -->\s*<style>.*?</style>\s*<script>.*?</script>(?:\s*<!-- /responsive-inject(?:-v\d+)? -->)?",
        "",
        content,
        flags=re.DOTALL,
    )
    final_content = re.sub(
        r"(<head[^>]*>)",
        r"\1\n" + snippet,
        new_content,
        count=1,
        flags=re.IGNORECASE,
    )
    if final_content != new_content:
        print(f"  Injected responsive enhancer into {filename}")
    return final_content


BACK_LINK_MARKER = "<!-- back-link-inject -->"

BACK_LINK_SNIPPET = (
    "<!-- back-link-inject -->"
    "<div style=\"font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;"
    'padding:6px 0 2px;font-size:0.78rem;">'
    f'<a href="{SITE_URL}/" style="color:#4f8ef7;text-decoration:none;font-weight:600;">'
    "&#8592; DataDashboard</a></div>"
)


def inject_back_link(content: str, filename: str) -> str:
    """Inject a 'back to homepage' link right after <body> in an analysis file content."""
    if BACK_LINK_MARKER in content:
        return content

    new_content = re.sub(
        r"(<body[^>]*>)",
        r"\1\n" + BACK_LINK_SNIPPET,
        content,
        count=1,
        flags=re.IGNORECASE,
    )
    if new_content != content:
        print(f"  Injected back-link into {filename}")
    return new_content


def inject_favicon(content: str, filename: str) -> str:
    """Inject favicon link into an analysis HTML file content if not already present."""
    if 'rel="icon"' in content or "rel='icon'" in content:
        return content  # already has one, leave it alone

    favicon_link = (
        f'\n  <link rel="icon" href="{SITE_URL}/favicon.ico" type="image/x-icon">'
    )

    # Insert just before </head>
    new_content = re.sub(
        r"(</head>)", favicon_link + r"\n\1", content, count=1, flags=re.IGNORECASE
    )
    if new_content != content:
        print(f"  Injected favicon into {filename}")
    return new_content


def inject_og_tags(content: str, filename: str, stem: str) -> str:
    """Inject og:image/twitter:image into an analysis HTML file content if not already present."""
    if "og:image" in content:
        return content  # already has one, leave it alone

    image_url = f"{SITE_URL}/previews/{stem}.png"

    # Extract title for og:title
    title_match = re.search(
        r"<title[^>]*>(.*?)</title>", content, re.IGNORECASE | re.DOTALL
    )
    title = (
        title_match.group(1).strip() if title_match else stem.replace("_", " ").title()
    )
    title = html.escape(html.unescape(title), quote=True)

    og_block = (
        f"\n  <!-- Open Graph / Social Sharing -->"
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
    new_content = re.sub(
        r"(</head>)", og_block + r"\n\1", content, count=1, flags=re.IGNORECASE
    )
    if new_content != content:
        print(f"  Injected og:image into {filename}")
    return new_content


def build_card(analysis: dict, index: int) -> str:
    color = ACCENT_COLORS[index % len(ACCENT_COLORS)]
    badges_html = "".join(
        f'<span class="badge">{html.escape(tag)}</span>' for tag in analysis["tags"]
    )
    desc_html = (
        f'<p class="card-desc">{html.escape(analysis["description"])}</p>'
        if analysis["description"]
        else ""
    )
    date_html = (
        f'<span class="card-date">{html.escape(analysis["date"])}</span>'
        if analysis["date"]
        else ""
    )
    return f"""      <a class="card" href="{html.escape(analysis['filename'], quote=True)}" style="--accent:{color}">
        <div class="card-top">
          <div class="card-title">{html.escape(analysis['title'])}</div>
          <div class="badges">{badges_html}</div>
        </div>
        {desc_html}
        <div class="card-footer">
          {date_html}
          <span class="card-link">View analysis →</span>
        </div>
      </a>"""


def build_html(analyses: list[dict]) -> str:
    from string import Template

    count = len(analyses)
    subtitle = (
        f'{count} analysis{"" if count == 1 else "es"}'
        if count
        else "No analyses yet — drop an HTML file here"
    )

    cards_html = "\n".join(build_card(a, i) for i, a in enumerate(analyses))
    empty_html = (
        '<div class="empty">No analyses found yet.<br>Add <code>.html</code> files to the repo root and push.</div>'
        if not analyses
        else ""
    )

    og_image_url = f"{SITE_URL}/previews/index.png"
    og_desc = (
        f'{count} analysis{"" if count == 1 else "es"} from various datasets and projects.'
        if count
        else "A hub for data analysis visualizations and insights."
    )

    template_path = Path(__file__).parent / "index_template.html"
    template_content = template_path.read_text(encoding="utf-8")
    template = Template(template_content)

    return template.safe_substitute(
        SITE_URL=SITE_URL,
        subtitle=subtitle,
        cards_html=cards_html,
        empty_html=empty_html,
        og_image_url=og_image_url,
        og_desc=og_desc,
    )


def main(argv: Optional[list[str]] = None):
    args = parse_args(argv)
    descriptions = load_descriptions()
    analyses = []

    # Process all HTML files, extract meta, and inject enhancements
    html_files = [p for p in ROOT.glob("*.html") if p.name.lower() not in EXCLUDE]
    # Sort files by modification time before we potentially write back and alter their mtime
    html_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    for filepath in html_files:
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            # Fallback for file read errors if any
            analyses.append(_fallback(filepath))
            continue

        # Extract meta
        meta = extract_meta(filepath, content, descriptions=descriptions)
        analyses.append(meta)

        # Inject enhancements
        new_content = inject_responsive(
            content, meta["filename"], args.responsive_preset
        )
        new_content = inject_back_link(new_content, meta["filename"])
        new_content = inject_favicon(new_content, meta["filename"])
        new_content = inject_og_tags(new_content, meta["filename"], filepath.stem)

        if new_content != content:
            filepath.write_text(new_content, encoding="utf-8")

    html = build_html(analyses)
    output = ROOT / "index.html"
    output.write_text(html, encoding="utf-8")
    print(f"Generated index.html with {len(analyses)} analysis file(s).")
    for a in analyses:
        print(f'  - {a["filename"]} → {a["title"]}')


if __name__ == "__main__":
    main()
