## 2024-05-24 - [Resolve Flaky Toast Wait Logic]
Coverage Gap: Playwright wait_for(state="visible") followed by standard assertions caused intermittent flaky tests.
Learning: Relying on generic assertion libraries instead of Playwright's expect() leads to race conditions when testing async components like toast notifications.
Assertion: Always use expect(locator).to_be_visible() combined with expect(locator).to_contain_text() to ensure reliable testing.
