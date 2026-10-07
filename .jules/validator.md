## 2026-10-07 - Fix Service Worker Cache Invalidation Race Condition
Coverage Gap: Service worker cache invalidation logic in tests/test_service_worker.py relied on an arbitrary 1000ms timeout to clear caches, which was susceptible to flaky behavior in CI.
Learning: Using page.wait_for_timeout introduces race conditions in testing environments where async operations like Service Worker cache deletion can vary in execution time.
Assertion: Instead of waiting an arbitrary duration, use `page.wait_for_function()` to actively poll and evaluate the expected state (e.g., verifying `caches.keys()` does not contain old caches) to ensure deterministic assertions.
