## 2026-05-11 - Mocking pathlib dynamically loaded modules

**Learning:** When using `importlib` to dynamically load a script as a module, standard `unittest.mock.patch` might need to be applied broadly to the original imported classes (like `pathlib.Path.exists` or `pathlib.Path.read_text`) rather than the local module's imported alias, because the dynamic loading can bypass some patching mechanics if not careful.

**Action:** When dynamically loading scripts for testing, use `patch('pathlib.Path.exists')` to safely intercept file system checks across the script execution without dirtying the test runner's state.
## 2026-05-16 - Dynamic extraction of HTML snippet versions
**Learning:** Hardcoding marker-based HTML snippet injection tags like `<!-- responsive-inject-v6 -->` in tests causes tests to fail unnecessarily when the core module's internal logic increments its snippet versioning scheme.
**Action:** When testing marker-based injection functions, dynamically extract the expected current marker from the module's configuration (like `module.RESPONSIVE_PRESETS['default']['marker']`) rather than hardcoding.
