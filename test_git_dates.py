from pathlib import Path
from deployment.generate_index import get_git_dates_batched

files = list(Path.cwd().glob('*.html'))
dates = get_git_dates_batched(files)
print("Keys in dates:")
for k in dates:
    print(repr(k))

print("\nFiles passed:")
for f in files:
    print(repr(f))
