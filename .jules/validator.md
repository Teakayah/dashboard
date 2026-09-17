## 2026-09-17 - Fix flaky test in test_interactivity.py
Coverage Gap: The `test_slider_updates_regional_levels` was flaky because it was reading `low_hull` immediately without checking if live data is loaded.
Learning: Getting the DOM inner text for an asynchronous component during load results in default state values which makes assertions fail if data changes asynchronously.
Assertion: Always assert an explicit expectation (e.g. `not_to_have_text("0.00")`) before parsing inner text values to guarantee test execution is properly synchronized with layout data loading.
