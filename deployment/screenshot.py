#!/usr/bin/env python3
"""
Take a 600x315 screenshot of every .html file in the repo root
and save it to previews/{stem}.png.
Called by GitHub Actions after the local HTTP server is started.
"""

import sys
import time
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
PORT = 8765


def main():
    pages = sorted(p.name for p in ROOT.glob('*.html'))
    if not pages:
        print('No HTML files found — nothing to screenshot.')
        return

    print(f'Pages to screenshot: {pages}')

    # Start local server
    server = subprocess.Popen(
        ['python3', '-m', 'http.server', str(PORT)],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(2)

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
