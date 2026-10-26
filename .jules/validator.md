## 2024-10-26 - UI Stabilization Flakes
Coverage Gap: Flaky UI layout test checks relying on time.sleep or wait_for_timeout.
Learning: Hardcoded sleep values fail consistently due to dynamic asynchronous browser APIs or resize events executing after delays or faster than expected.
Assertion: Used page.wait_for_function to poll slider window layouts directly within the browser instead of timeout delays.
