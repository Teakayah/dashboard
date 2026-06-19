from pathlib import Path
from deployment.generate_feed import _get_batched_git_isos

files = list(Path.cwd().glob('*.html'))
dates = _get_batched_git_isos(files)
print("Keys in dates:")
for k in dates:
    print(repr(k))

print("\nFiles passed:")
for f in files:
    print(repr(f))
