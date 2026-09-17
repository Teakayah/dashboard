## 2026-09-17 - Prevent Untracked Artifact Pollution
**Learning:** During test-driven development, running scripts directly (like `generate_icons.py`) or creating temporary scripts (like `test_pixel.py`) can generate untracked binary files (e.g., `test_100.png`) in the root directory.
**Action:** Always run `git status` before requesting a code review or submitting to identify and remove (`rm`) any untracked, non-source artifacts to prevent repository pollution.
