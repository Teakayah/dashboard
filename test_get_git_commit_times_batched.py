from pathlib import Path
from deployment.screenshot import get_git_commit_times_batched

files = list(Path.cwd().glob('*.html'))
paths = [f.name for f in files]
paths.extend([f"previews/{f.stem}.png" for f in files])
dates = get_git_commit_times_batched(paths)

print("Keys in dates:")
for k in dates:
    print(repr(k), type(k))
