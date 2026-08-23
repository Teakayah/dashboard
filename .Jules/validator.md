## 2026-08-21 - Mocking Sequential Event Handlers
Coverage Gap: Failing tests due to weak assertions in sequential callback tests sharing a mock.
Learning: Replacing `assert_any_call` with `assert_called_once_with` on a shared mock causes strict assertion failures unless the call history is explicitly cleared between invocations.
Assertion: Call `mock.reset_mock()` between invocations to ensure accurate strict assertions and isolate sequential checks.
