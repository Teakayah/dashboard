## 2026-05-10 - PosixPath Mocking in Python 3.12+
**Learning:** In Python 3.12+, `PosixPath` properties and methods cannot be mocked directly on an instance using `patch.object(module_var, 'exists')` because it raises an `AttributeError: 'PosixPath' object attribute 'exists' is read-only`.
**Action:** When mocking path operations, use the global patch string `'pathlib.Path.exists'` rather than patching the specific instantiated path object.

## 2026-05-10 - Testing Orchestrator Scripts
**Learning:** Orchestrator scripts (like `refresh.py` or pipelines) can have massive side effects if they run subprocesses like `git` or other python scripts during the test suite. If a mock fails, it will mutate the workspace (`index.html`, `feed.xml`, etc.).
**Action:** When adding tests for deployment or orchestrator scripts, rigorously mock all `subprocess.run` calls to prevent test execution from accidentally modifying tracked repository files and creating a dirty state.
