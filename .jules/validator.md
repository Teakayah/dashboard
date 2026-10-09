## 2026-10-09 - Fix Flaky Service Worker Cache Test
Coverage Gap: Service worker cache clearing test was flaky due to arbitrary timeouts.
Learning: Asynchronous browser APIs like caches.keys() shouldn't be tested with arbitrary wait_for_timeout() delays, as they are non-deterministic and can flake on slower runners.
Assertion: Replaced hardcoded wait_for_timeout(1000) with a page.wait_for_function() that explicitly polls the browser state until the condition (!keys.includes) is met.
