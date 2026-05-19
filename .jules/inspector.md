## 2026-05-11 - Mocking pathlib dynamically loaded modules

**Learning:** When using `importlib` to dynamically load a script as a module, standard `unittest.mock.patch` might need to be applied broadly to the original imported classes (like `pathlib.Path.exists` or `pathlib.Path.read_text`) rather than the local module's imported alias, because the dynamic loading can bypass some patching mechanics if not careful.

**Action:** When dynamically loading scripts for testing, use `patch('pathlib.Path.exists')` to safely intercept file system checks across the script execution without dirtying the test runner's state.
## 2024-05-18 - [Dynamic Test Assertions]
**Learning:** Tests relying on HTML injection should dynamically lookup expected markers using the module configuration (like `module.RESPONSIVE_PRESETS["default"]["marker"]`) rather than hardcoding versions. This prevents tests from failing unnecessarily when the internal logic increments its snippet versioning scheme.
**Action:** Whenever testing string injection or generation in Python scripts, identify the source of truth for the injected strings (e.g. constant configurations) and use those variables in assertions.
