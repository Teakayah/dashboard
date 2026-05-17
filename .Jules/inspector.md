## 2026-05-11 - Mocking pathlib dynamically loaded modules

**Learning:** When using `importlib` to dynamically load a script as a module, standard `unittest.mock.patch` might need to be applied broadly to the original imported classes (like `pathlib.Path.exists` or `pathlib.Path.read_text`) rather than the local module's imported alias, because the dynamic loading can bypass some patching mechanics if not careful.

**Action:** When dynamically loading scripts for testing, use `patch('pathlib.Path.exists')` to safely intercept file system checks across the script execution without dirtying the test runner's state.
## 2026-05-17 - Extracting Marker Configuration
**Learning:** When testing marker-based HTML injection logic, hardcoding the marker string (e.g. `<!-- responsive-inject-v5 -->`) in tests leads to test breakage whenever the production version is incremented.
**Action:** Extract the expected marker dynamically from the module's configuration (e.g. `module.RESPONSIVE_PRESETS['default']['marker']`) to ensure the test scales gracefully with codebase updates.
