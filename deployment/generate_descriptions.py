#!/usr/bin/env python3
"""
Generate AI descriptions for HTML analysis files and save them to descriptions.json.

Run this locally whenever you add or update an analysis page. The output file is
committed to the repo so that GitHub Actions never needs to call Ollama.

Configuration (via environment variables or a .env file):
    OLLAMA_URL    Ollama HTTP endpoint  (default: http://localhost:11434/api/generate)
    OLLAMA_MODEL  Model to use          (default: gemma4:e4b)

Usage:
    python deployment/generate_descriptions.py              # update missing entries
    python deployment/generate_descriptions.py --force      # regenerate all entries
    python deployment/generate_descriptions.py --file foo.html  # single file
"""

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
DESCRIPTIONS_FILE = ROOT / 'descriptions.json'
EXCLUDE = {'index.html'}

OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434/api/generate')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'gemma4:e4b')
OLLAMA_TIMEOUT = 30  # seconds


def ollama_describe(content: str, filename: str) -> str:
    """Ask local Ollama to generate a one-sentence card description from HTML content."""
    snippet = content[:8_000]
    prompt = (
        f"You are summarizing a data analysis HTML page called '{filename}'. "
        "In one sentence (max 120 characters), describe what data or insights this page shows. "
        "Be specific: mention the dataset, metric, or topic visualized. "
        "Reply with only the sentence — no quotes, no intro.\n\n"
        f"HTML:\n{snippet}"
    )
    payload = json.dumps({'model': OLLAMA_MODEL, 'prompt': prompt, 'stream': False}).encode()
    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
            result = json.loads(resp.read()).get('response', '').strip()
            return result[:117] + '…' if len(result) > 120 else result
    except Exception as e:
        print(f'  [warn] Ollama unavailable for {filename}: {e}')
        return ''


def load_descriptions() -> dict:
    if DESCRIPTIONS_FILE.exists():
        return json.loads(DESCRIPTIONS_FILE.read_text(encoding='utf-8'))
    return {}


def save_descriptions(descriptions: dict) -> None:
    DESCRIPTIONS_FILE.write_text(
        json.dumps(descriptions, indent=2, ensure_ascii=False) + '\n',
        encoding='utf-8',
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.strip())
    parser.add_argument(
        '--force',
        action='store_true',
        help='Regenerate descriptions even for files that already have one.',
    )
    parser.add_argument(
        '--file',
        metavar='FILENAME',
        help='Process a single HTML file by name (e.g. my_analysis.html).',
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    descriptions = load_descriptions()

    if args.file:
        targets = [ROOT / args.file]
    else:
        targets = sorted(ROOT.glob('*.html'), key=lambda p: p.stat().st_mtime, reverse=True)

    updated = 0
    for filepath in targets:
        if filepath.name.lower() in EXCLUDE:
            continue
        if not filepath.exists():
            print(f'  [skip] {filepath.name} not found')
            continue
        if not args.force and descriptions.get(filepath.name):
            print(f'  [skip] {filepath.name} already has a description')
            continue

        print(f'  Generating description for {filepath.name}…')
        content = filepath.read_text(encoding='utf-8', errors='ignore')
        desc = ollama_describe(content, filepath.name)
        if desc:
            descriptions[filepath.name] = desc
            print(f'    → {desc}')
            updated += 1
        else:
            print(f'    → (no description generated)')

    save_descriptions(descriptions)
    print(f'\nDone. {updated} description(s) updated in {DESCRIPTIONS_FILE.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
