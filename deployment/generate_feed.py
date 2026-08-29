#!/usr/bin/env python3
"""
Generate an Atom feed (feed.xml) for the DataDashboard site.

Each analysis page becomes a feed entry, sorted newest-first by git commit date.
The feed is regenerated on every deploy so subscribers always see the latest updates.
"""

import html as html_lib
import json
import re
import concurrent.futures
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
EXCLUDE = {'index.html'}
SITE_URL = 'https://teakayah.github.io/dashboard'
FEED_PATH = ROOT / 'feed.xml'
DESCRIPTIONS_FILE = ROOT / 'descriptions.json'


def _load_descriptions() -> dict:
    if DESCRIPTIONS_FILE.exists():
        return json.loads(DESCRIPTIONS_FILE.read_text(encoding='utf-8'))
    return {}


try:
    from git_utils import _get_batched_git_isos
except ImportError:
    from deployment.git_utils import _get_batched_git_isos


def _extract_title(content: str, stem: str) -> str:
    m = re.search(
        r'''
        <title[^>]*>  # Capture the opening title tag with optional attributes
        (.*?)         # Group 1: Non-greedily capture the inner content
        </title>      # Capture the closing title tag
        ''',
        content, re.IGNORECASE | re.DOTALL | re.VERBOSE
    )
    raw = m.group(1).strip() if m else stem.replace('_', ' ').title()
    return (raw
            .replace('&amp;', '&').replace('&lt;', '<')
            .replace('&gt;', '>').replace('&#39;', "'"))


def _extract_description(content: str, filename: str, descriptions: dict) -> str:
    # 1. <meta name="description">
    m = re.search(
        r'''
        <meta[^>]*                  # Matches the opening <meta tag and any attributes before 'name'
        name=["\']description["\']  # Matches the name attribute with either single or double quotes
        [^>]*                       # Matches any intermediate attributes before 'content'
        content=["\'](.*?)["\']     # Group 1: Non-greedily captures the actual description text
        ''',
        content, re.IGNORECASE | re.VERBOSE
    )
    if m:
        return m.group(1).strip()

    # 2. Subtitle element
    # Extract inner content from elements with the 'subtitle' class.
    m = re.search(
        r'''
        <([a-zA-Z0-9]+)                              # Group 1: Capture the HTML opening tag name (e.g., div, span, p)
        [^>]*class=["\'][^"\']*subtitle[^"\']*["\']  # Ensure the tag has a class attribute containing 'subtitle'
        [^>]*>                                       # Match the remainder of the opening tag
        (.*?)                                        # Group 2: Non-greedily capture the inner content
        </\1>                                        # Use \1 backreference to match the exact closing tag from Group 1
        ''',
        content, re.IGNORECASE | re.DOTALL | re.VERBOSE,
    )
    if m:
        text = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        text = html_lib.unescape(re.sub(r'\s+', ' ', text))
        return text[:120] + '…' if len(text) > 120 else text

    # 3. Pre-generated description from descriptions.json
    return descriptions.get(filename, '')


def _build_entry(filepath: Path, descriptions: dict, git_iso: str) -> dict:
    """Return a dict with all fields needed to render a feed <entry>."""
    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        content = ''

    title = _extract_title(content, filepath.stem)
    description = _extract_description(content, filepath.name, descriptions)
    updated = git_iso
    stem = filepath.stem
    page_url = f'{SITE_URL}/{filepath.name}'
    preview_url = f'{SITE_URL}/previews/{stem}.png'

    return {
        'title': title,
        'url': page_url,
        'id': page_url,
        'updated': updated,
        'summary': description,
        'preview_url': preview_url,
    }


def _atom_entry(entry: dict) -> str:
    preview_img = (
        f'&lt;img src="{html_lib.escape(entry["preview_url"], quote=True)}" '
        f'alt="{html_lib.escape(entry["title"], quote=True)}" '
        f'style="max-width:100%;border-radius:8px;margin-bottom:8px;" /&gt;'
        if entry['preview_url'] else ''
    )
    summary_html = f'&lt;p&gt;{html_lib.escape(entry["summary"], quote=True)}&lt;/p&gt;' if entry['summary'] else ''

    return f'''\
  <entry>
    <title>{html_lib.escape(entry['title'], quote=True)}</title>
    <link href="{html_lib.escape(entry['url'], quote=True)}" />
    <id>{html_lib.escape(entry['id'], quote=True)}</id>
    <updated>{entry['updated']}</updated>
    <summary type="text">{html_lib.escape(entry['summary'], quote=True)}</summary>
    <content type="html">{preview_img}{summary_html}</content>
  </entry>'''


def build_feed(entries: list[dict]) -> str:
    # Feed updated = most recent entry updated timestamp
    feed_updated = (
        max(e['updated'] for e in entries)
        if entries
        else datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    )

    entries_xml = '\n'.join(_atom_entry(e) for e in entries)

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>DataDashboard</title>
  <subtitle>Statistics Canada data visualizations</subtitle>
  <link href="{SITE_URL}/" />
  <link rel="self" type="application/atom+xml" href="{SITE_URL}/feed.xml" />
  <id>{SITE_URL}/</id>
  <updated>{feed_updated}</updated>
  <author>
    <name>DataDashboard</name>
    <uri>{SITE_URL}/</uri>
  </author>
{entries_xml}
</feed>
'''


def main() -> None:
    descriptions = _load_descriptions()

    html_files_unsorted = [p for p in ROOT.glob('*.html') if p.name.lower() not in EXCLUDE]
    git_isos = _get_batched_git_isos(html_files_unsorted)
    fallback_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    html_files = sorted(
        html_files_unsorted,
        key=lambda p: git_isos.get(p, fallback_time),
        reverse=True,
    )

    with concurrent.futures.ThreadPoolExecutor() as executor:
        entries = list(executor.map(
            lambda f: _build_entry(f, descriptions, git_isos.get(f, fallback_time)),
            html_files
        ))

    feed_xml = build_feed(entries)
    FEED_PATH.write_text(feed_xml, encoding='utf-8')

    print(f'Generated {FEED_PATH.relative_to(ROOT)} with {len(entries)} entries.')
    for e in entries:
        print(f'  - {e["title"]} ({e["updated"][:10]})')


if __name__ == '__main__':  # pragma: no cover
    main()
