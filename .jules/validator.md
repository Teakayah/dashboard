## 2026-10-12 - Flaky Playwright UI Layout Stabilizations
Coverage Gap: Flaky UI layout test due to manual python-side `page.wait_for_timeout()` loop tracking min/max dimensions continuously.
Learning: Python-side loop sleeping and tracking dimensions over time incorrectly flags the unstable transition frames. If dimensions change, min/max window tracking must be reset.
Assertion: Replace `page.wait_for_timeout()` sleep loops with `page.wait_for_function()` executing javascript that polls and actively resets tracking bounds whenever instability is detected.
