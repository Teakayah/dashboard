## 2026-09-19 - Test UI State Reset on Destructive Actions
Coverage Gap: The `#export-db` button state was unverified when the `#clear-data` destructive action was triggered, allowing potential regressions where actions are allowed on cleared data.
Learning: UI state resets accompanying destructive actions (like clearing storage) need dedicated tests to ensure downstream dependent controls are properly disabled.
Assertion: Simulate the destructive action and use `expect(locator).to_be_disabled()` to reliably verify the UI element falls back to a disabled state.
