## 2024-05-04 - Fix test_screenshot.py mock command line arguments
**Learning:** When testing a Python script using `argparse` that's invoked dynamically, `sys.argv` defaults to whatever pytest was started with, causing `unrecognized arguments` failures.
**Action:** Patch `sys.argv` in the test to provide predictable command-line arguments for scripts loaded with `importlib.util`.
