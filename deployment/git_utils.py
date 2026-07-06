import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent.resolve()

def get_git_log_batched(files: list[str], format_code: str) -> dict[str, str]:
    """
    Return git log timestamps for multiple files in a single call.
    format_code: Git log format code, e.g., '%ci', '%cI', '%ct'.
    Returns a dict mapping the string filename to the parsed timestamp string.
    """
    if not files:
        return {}

    dates = {}
    try:
        # files are strings, assumed to be relative to ROOT
        cmd = ['git', 'log', f'--format=TS:{format_code}', '--name-only', '--'] + files
        # Notice we removed check=True because git log might fail on some files and we still want to parse
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))

        current_ts = None
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith('TS:'):
                current_ts = line[3:]
            elif current_ts:
                # Store by string filename (e.g. "index.html" or "previews/test.png")
                if line not in dates:
                    dates[line] = current_ts
    except Exception:
        pass

    return dates

def get_git_dates_batched(files: list[Path]) -> dict[Path, str]:
    """Return 'Mon YYYY' from git log for multiple files in a single call; fall back to mtime."""
    if not files:
        return {}
    dates = {}

    # Convert Path objects to string paths relative to ROOT
    rel_paths = []
    for f in files:
        if f.is_absolute():
            try:
                rel_paths.append(str(f.relative_to(ROOT)))
            except ValueError:
                rel_paths.append(str(f.name))
        else:
            rel_paths.append(str(f))

    raw_dates = get_git_log_batched(rel_paths, '%ci')

    for line, current_ts in raw_dates.items():
        p = ROOT / line
        if p not in dates:
            try:
                dates[p] = datetime.fromisoformat(current_ts).strftime('%b %Y')
            except Exception:
                pass

    # Fallback to mtime for files not in git or not returned
    for f in files:
        if f not in dates:
            try:
                mtime = f.stat().st_mtime
                dates[f] = datetime.fromtimestamp(mtime).strftime('%b %Y')
            except Exception:
                pass
    return dates

def _get_batched_git_isos(files: list[Path]) -> dict[Path, str]:
    """Return ISO 8601 timestamps for multiple files from git log."""
    if not files:
        return {}

    dates = {}
    rel_paths = [f.name for f in files]
    raw_dates = get_git_log_batched(rel_paths, '%cI')

    file_names = {f.name: f for f in files}

    for line, current_ts in raw_dates.items():
        if line in file_names and file_names[line] not in dates:
            dates[file_names[line]] = current_ts

    return dates

def get_git_commit_times_batched(paths: list[str]) -> dict[str, int]:
    """Return the Unix timestamp of the last commit touching each path."""
    if not paths:
        return {}

    times = {}
    raw_dates = get_git_log_batched(paths, '%ct')

    for line, current_ts in raw_dates.items():
        try:
            times[line] = int(current_ts)
        except Exception:
            pass

    return times
