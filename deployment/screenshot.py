#!/usr/bin/env python3
"""
Take a 600x315 screenshot of every .html file in the repo root
and save it to previews/{stem}.png.
Called by GitHub Actions after the local HTTP server is started.
"""

import argparse
import socket
import sys
import time
import subprocess
from deployment.git_utils import get_git_commit_times_batched
from pathlib import Path

# Import centralized configuration
try:
    from config import ROOT
except ImportError:
    from deployment.config import ROOT

PORT = 8765




def needs_screenshot(name: str, html_ts: int, png_ts: int, force: bool = False) -> bool:
    """Return True if the page's preview is missing or older than the page's last commit."""
    if force:
        return True
    preview = ROOT / 'previews' / f'{Path(name).stem}.png'
    if not preview.exists():
        return True

    # Check if the preview file exists on disk and get its mtime as fallback if not in git
    if png_ts == 0:
        preview_path = f'previews/{preview.name}'
        png_ts = int((ROOT / preview_path).stat().st_mtime)
    
    if html_ts == 0:
        html_ts = int((ROOT / name).stat().st_mtime)
        
    return html_ts > png_ts


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip())
    parser.add_argument('--force', action='store_true', help='Force regenerate all screenshots')
    args = parser.parse_args()

    all_pages = sorted(p.name for p in ROOT.glob('*.html'))
    if not all_pages:
        print('No HTML files found — nothing to screenshot.')
        return

    # Pre-fetch git commit times for all pages and their corresponding previews
    paths_to_check = all_pages.copy()
    for p in all_pages:
        paths_to_check.append(f'previews/{Path(p).stem}.png')

    git_times = get_git_commit_times_batched(paths_to_check)

    pages = []
    skipped = []
    for p in all_pages:
        html_ts = git_times.get(str(p), 0)
        png_ts = git_times.get(f'previews/{Path(p).stem}.png', 0)
        if needs_screenshot(p, html_ts, png_ts, force=args.force):
            pages.append(p)
        else:
            skipped.append(p)

    if skipped:
        print(f'Skipped (up-to-date): {skipped}')
    if not pages:
        print('All previews are up-to-date — nothing to do.')
        return

    print(f'Pages to screenshot: {pages}')

    # Start local server
    server = subprocess.Popen(
        ['python3', '-m', 'http.server', str(PORT), '--bind', '127.0.0.1'],
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
                # Use a slightly larger viewport for better capture, then we could crop if needed
                # but 600x315 is the OG standard
                page = browser.new_page(viewport={'width': 800, 'height': 420})
                page.goto(f'http://localhost:{PORT}/{name}')
                
                # Wait for any canvas or major content
                try:
                    page.wait_for_selector('canvas, .grid, .container', timeout=10000)
                    # Give charts a moment to animate
                    page.wait_for_timeout(1000)
                except Exception:
                    pass
                
                # Capture the top of the page (which usually contains the main viz)
                # and scale to 600x315
                page.screenshot(path=str(out), clip={'x': 0, 'y': 0, 'width': 800, 'height': 420})
                
                # Note: Playwright doesn't have a built-in resize on capture, 
                # so we capture 800x420 which is the same aspect ratio as 600x315.
                
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


if __name__ == '__main__':  # pragma: no cover
    main()
