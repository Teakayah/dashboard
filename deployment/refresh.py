#!/usr/bin/env python3
"""
Local weekly data refresh pipeline.

Runs each step in order, aborts on any failure:

  1. Download Stats Canada CSVs       (update_statcan_data.py)
  2. Rebuild analysis HTML data       (rebuild_analyses.py)
  3. Regenerate AI descriptions       (generate_descriptions.py --force)
  4. Rebuild index.html               (generate_index.py)
  5. Rebuild feed.xml                 (generate_feed.py)
  6. Run test suite                   (pytest tests/)
  7. Commit + push to dev branch      (triggers CI → main)

Usage:
    python3 deployment/refresh.py
    python3 deployment/refresh.py --no-push            # dry run: skip git push
    python3 deployment/refresh.py --no-descriptions    # skip Ollama step
    python3 deployment/refresh.py --force-descriptions # regenerate all descriptions

Schedule locally with launchd (macOS):
    Add a LaunchAgent plist that runs this script weekly.
    See: https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html
"""

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
DEPLOY = ROOT / 'deployment'
STATUS_FILE = ROOT / 'source' / '.update_result.json'


# ── Helpers ────────────────────────────────────────────────────────────────────

def _header(step: int, total: int, title: str) -> None:
    print(f'\n── Step {step}/{total}: {title} {"─" * max(0, 60 - len(title))}')


def _run(*args: str, allow_nonzero: bool = False) -> int:
    """Run a subprocess, stream output live, return exit code."""
    result = subprocess.run(args, cwd=str(ROOT))
    if result.returncode != 0 and not allow_nonzero:
        print(f'\n✗  Command failed (exit {result.returncode}): {" ".join(args)}')
        sys.exit(result.returncode)
    return result.returncode


def _git(*args: str) -> str:
    """Run a git command and return stdout (stripped)."""
    result = subprocess.run(
        ['git', *args], capture_output=True, text=True, cwd=str(ROOT)
    )
    return result.stdout.strip()


# ── Pipeline ───────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.strip())
    parser.add_argument('--no-push', action='store_true',
                        help='Run all steps but skip git commit and push.')
    parser.add_argument('--no-descriptions', action='store_true',
                        help='Skip the Ollama description generation step.')
    parser.add_argument('--force-descriptions', action='store_true',
                        help='Regenerate ALL descriptions, not just new ones.')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    skip_descriptions = args.no_descriptions
    total_steps = 6 if skip_descriptions else 7
    step = 0

    print('=' * 62)
    print('  DataDashboard — weekly data refresh')
    print(f'  {date.today()}')
    print('=' * 62)

    # 1. Download Stats Canada CSVs
    step += 1
    _header(step, total_steps, 'Download Stats Canada CSVs')
    _run('python3', str(DEPLOY / 'update_statcan_data.py'), allow_nonzero=True)

    # Read the status file written by update_statcan_data.py
    if not STATUS_FILE.exists():
        print('\n  ✗  Status file not found after download — aborting.')
        sys.exit(1)

    status = json.loads(STATUS_FILE.read_text())
    errors = [t for t in status.get('tables', []) if 'error' in t]
    updated_tables = [t['id'] for t in status.get('tables', []) if t.get('updated')]

    if errors:
        ids = [e['id'] for e in errors]
        print(f'\n  ⚠  Download errors for table(s): {ids}')
        print('     Check your internet connection and retry.')

    if not status.get('any_updated'):
        print('\n  Stats Canada has no new data since the last refresh.')
        print('  Nothing to process. Run again next week.')
        print('\n' + '=' * 62 + '\n')
        sys.exit(0)

    print(f'\n  Updated tables: {updated_tables}')

    # 2. Rebuild analysis HTML data constants
    step += 1
    _header(step, total_steps, 'Rebuild analysis HTML data')
    _run('python3', str(DEPLOY / 'rebuild_analyses.py'), allow_nonzero=True)

    # 3. Regenerate AI descriptions (optional)
    if not skip_descriptions:
        step += 1
        _header(step, total_steps, 'Regenerate AI descriptions (Ollama)')
        desc_args = ['python3', str(DEPLOY / 'generate_descriptions.py')]
        if args.force_descriptions:
            desc_args.append('--force')
        _run(*desc_args)

    # 4. Rebuild index.html
    step += 1
    _header(step, total_steps, 'Rebuild index.html')
    _run('python3', str(DEPLOY / 'generate_index.py'))

    # 5. Rebuild feed.xml
    step += 1
    _header(step, total_steps, 'Rebuild feed.xml')
    _run('python3', str(DEPLOY / 'generate_feed.py'))

    # 6. Run test suite
    step += 1
    _header(step, total_steps, 'Run test suite')
    _run('python3', '-m', 'pytest', 'tests/', '-v', '--tb=short')

    # 7. Commit + push to dev
    step += 1
    _header(step, total_steps, 'Commit + push to dev')

    if args.no_push:
        print('  --no-push set: skipping git commit and push.')
    else:
        status = _git('status', '--porcelain')
        if not status:
            print('  Nothing to commit — no changes since last push.')
        else:
            today = date.today().isoformat()
            msg = f'chore: weekly data refresh [{today}]'
            _run('git', 'add',
                 'employment_rate_canada.html',
                 'nhpi_big6_comparison.html',
                 'descriptions.json',
                 'index.html',
                 'feed.xml')
            _run('git', 'commit', '-m', msg)
            _run('git', 'push', 'origin', 'dev')
            print(f'\n  Pushed to dev → CI will merge to main and take screenshots.')

    print('\n' + '=' * 62)
    print('  ✓  Refresh complete')
    print('=' * 62 + '\n')


if __name__ == '__main__':
    main()
