## 2026-05-22 - [Mocking subprocess.check_output in deployment script]
Coverage Gap: The `_git` helper in `deployment/refresh.py` was not properly handling or testing `subprocess.check_output` and `subprocess.CalledProcessError`.
Learning: When a user requests testing for a specific snippet that differs from the existing codebase, it is critical to align the codebase to the intended snippet logic before writing tests for it to properly fulfill the prompt's structural and error-handling requirements.
Assertion: Replace `subprocess.run` with `subprocess.check_output`, wrap it in a `try...except subprocess.CalledProcessError` block, and verify test assertions use `.side_effect = subprocess.CalledProcessError(...)` when mocking to guarantee exact exception catching semantics.
