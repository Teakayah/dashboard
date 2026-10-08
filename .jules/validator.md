
## 2026-10-08 - Fix flaky service worker cache test
Coverage Gap: Service worker cache invalidation tests occasionally failed in CI.
Learning: Hardcoded `page.wait_for_timeout` is unreliable for asynchronous browser APIs like `caches.keys()`. Network and CPU constraints in CI cause cache cleanup to take varying amounts of time, leading to flaky assertions.
Assertion: Use `page.wait_for_function(...)` to continually poll the cache state directly within the browser until the stale caches are removed, instead of guessing an arbitrary timeout.
