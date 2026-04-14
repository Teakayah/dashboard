#!/usr/bin/env python3
"""
Take a 600x315 screenshot of every .html file in the repo root
and save it to previews/{stem}.png.
Called by GitHub Actions after the local HTTP server is started.
"""

import socket
import sys
import time
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
PORT = 8765


def _git_commit_time(path: str) -> int:
    """Return the Unix timestamp of the last commit touching `path`, or 0."""
    result = subprocess.run(
        ['git', 'log', '-1', '--format=%ct', '--', path],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    stamp = result.stdout.strip()
    return int(stamp) if stamp else 0


def needs_screenshot(name: str) -> bool:
    """Return True if the page's preview is missing or older than the page's last commit."""
    preview = ROOT / 'previews' / f'{Path(name).stem}.png'
    if not preview.exists():
        return True
    html_ts = _git_commit_time(name)
    png_ts = _git_commit_time(f'previews/{preview.name}')
    return html_ts > png_ts


def main():
    all_pages = sorted(p.name for p in ROOT.glob('*.html'))
    if not all_pages:
        print('No HTML files found — nothing to screenshot.')
        return

    pages = [p for p in all_pages if needs_screenshot(p)]
    skipped = [p for p in all_pages if p not in pages]

    if skipped:
        print(f'Skipped (up-to-date): {skipped}')
    if not pages:
        print('All previews are up-to-date — nothing to do.')
        return

    print(f'Pages to screenshot: {pages}')

    # Start local server
    server = subprocess.Popen(
        ['python3', '-m', 'http.server', str(PORT)],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(40):
        try:
            socket.create_connection(('localhost', PORT), timeout=0.5).close()
            break
        except OSError:
            time.sleep(0.25)
    else:
        server.terminate()
        sys.exit(f'HTTP server did not start on localhost:{PORT}')

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        server.terminate()
        sys.exit('Playwright is not installed. Run: pip install playwright && python -m playwright install chromium')

    (ROOT / 'previews').mkdir(exist_ok=True)

    failed = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for name in pages:
            stem = Path(name).stem
            out = ROOT / 'previews' / f'{stem}.png'
            try:
                page = browser.new_page(viewport={'width': 600, 'height': 315})
                page.goto(f'http://localhost:{PORT}/{name}')
                try:
                    page.wait_for_load_state('networkidle', timeout=8000)
                except Exception:
                    pass  # CDN assets may be slow; screenshot whatever loaded
                page.screenshot(path=str(out))
                page.close()
                print(f'  OK  previews/{stem}.png  ({out.stat().st_size} bytes)')
            except Exception as exc:
                print(f'  FAIL  {name}: {exc}')
                failed.append(name)
        browser.close()

    server.terminate()
    server.wait()

    if failed:
        sys.exit(f'Failed to screenshot: {failed}')


if __name__ == '__main__':
    main()
