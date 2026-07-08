## 2026-05-02 - Custom Drop Zones Require Manual Keyboard Support
**Learning:** When building custom file drop zones using `div` elements, they lack native keyboard interactivity. Even if they accept click events, screen reader and keyboard-only users cannot focus or activate them without explicit `tabindex`, `role="button"`, and manual `keydown` event listeners for 'Enter' and 'Space' keys.
**Action:** Always ensure custom interactive areas meant to act like buttons have `tabindex="0"`, `role="button"`, clear `:focus-visible` styles, and keyboard event handlers that trigger the same functionality as their click events.
## 2026-05-04 - ARIA Labels for Icon-Only and Contextual Form Elements
**Learning:** In accessibility-focused code, always ensure that form elements (like `<input>` and `<select>`) have an explicit `aria-label` when a visible label is missing or when the context isn't implicitly clear to screen readers (e.g., search bars, icon-only buttons, or complex form structures like join assistants).
**Action:** When auditing forms, specifically look for `<input type="search">`, `<select>`, and `<textarea>` elements without associated `<label>` tags and add `aria-label` attributes describing their purpose.
## 2026-05-15 - Interactive Elements Hidden by Opacity Require Focus Visibility
**Learning:** Interactive elements (like the fullscreen button) that are hidden via `opacity: 0` until hovered are inaccessible to keyboard-only users who cannot "hover" to see them when they tab to the element.
**Action:** Always add a `:focus-visible` selector that sets `opacity: 1` and a clear outline when relying on hover states to reveal interactive controls.
## 2026-05-16 - Explicit ARIA Labels for Injected Action Elements
**Learning:** Dynamically injected elements meant to serve as interactive buttons (e.g., clicking a column name to insert it into a SQL editor) often lack the semantic context that screen readers rely on. Without an explicit `aria-label`, a screen reader user only hears the text content (e.g., "id (INTEGER)"), not the action it performs.
**Action:** Always add an explicit `aria-label` describing the full action (e.g., "Insert column id into SQL editor") to dynamically generated interactive spans or divs to clarify their purpose for assistive technologies.
## 2026-05-18 - Managing Dynamic Tooltips for Disabled States
**Learning:** Adding `title` tooltips to `disabled` buttons improves accessibility by explaining why an action is unavailable. However, if the tooltip isn't dynamically cleared when the button becomes enabled, users see outdated/confusing explanations (e.g., "Requires a valid query" appearing on an enabled "Run Query" button).
**Action:** When adding explanatory tooltips to disabled buttons, always pair the `title` attribute management with the JS logic that toggles the `disabled` property. Clear the `title` (or set it to the normal action description) when `disabled = false`, and restore the explanation when `disabled = true`.
## 2026-05-19 - Dispatching Events for Programmatic Input Changes
**Learning:** When building vanilla JavaScript UIs, changing an input's value programmatically (e.g., `sqlInput.value = '...'`) does not natively fire the `input` or `change` events. This causes reactive UI state (like disabling/enabling a submit button based on the input's length) to become out of sync.
**Action:** When adding real-time validation via `input` event listeners, always audit the codebase for programmatic assignments to that element's `.value` and explicitly append `.dispatchEvent(new Event('input'))` after them to ensure UI consistency.
## 2026-05-21 - Keyboard Shortcut Discoverability
**Learning:** Keyboard shortcuts improve power-user experience but are often hidden.
**Action:** Always provide visual hints (e.g., dynamic title attributes) when implementing keyboard shortcuts.

## 2026-05-22 - Replacing Custom Tabs with Native Buttons Requires Style Resets
**Learning:** When improving accessibility by converting custom `<div>` or `<span>` tabs into native `<button role="tab">` elements to gain free keyboard and focus support, the browser's default button styles (background, borders, font-family, and outline) will break the existing UI design if not explicitly overridden, even if the elements share the same CSS classes.
**Action:** When replacing custom elements with native buttons for accessibility, always inject specific CSS resets (e.g., `background: transparent; border: none; font-family: inherit; outline: none;`) alongside the new tags so that existing class-based styling continues to render identically.

## 2026-05-22 - Fix deferred accessibility rules (axe-core color-contrast, scrollable-region-focusable)
**Learning:** Axe-core color contrast failures inside charts or custom components can be tricky. Explicitly map UI data elements (like map dots, labels) to darker accessible colors by adjusting the color variables or style attributes directly. For `scrollable-region-focusable`, it was important to identify that `.tabs` acting as scrollable containers must also be explicitly keyboard accessible. Native HTML `<button>` works, or explicitly using `role="tab"` and `tabindex` with Javascript focus handlers on `<div>` elements satisfies accessibility.
**Action:** When working on custom interactive elements or styling from third-party themes, proactively verify the contrast ratio (`>= 4.5:1` for regular text) against both light and dark mode variables. When fixing `axe-core` tests during pytest runs, if error logs truncate the elements, spin up a fast Playwright script to fetch `axe.run()` and print full `nodes`.
## 2026-05-24 - Focus Visible Styles
**Learning:** Default browser focus rings are frequently insufficient or completely hidden for native `<button>` and `<input>` elements in this application's custom CSS, requiring explicit `:focus-visible` styles with custom outlines and offsets to guarantee keyboard accessibility.
**Action:** Always verify keyboard focus visibility using tab navigation and explicitly define `:focus-visible` styles (e.g., `outline: 2px solid var(--primary); outline-offset: 2px;`) rather than relying on default browser behaviors.

## 2026-06-01 - Global Keyboard Shortcut Hints and Focus States
**Learning:** When adding a global keyboard shortcut (like `/` to focus an input), it's crucial to visually indicate the shortcut exists without obstructing the UI. Additionally, a shortcut hint over an input should hide when the input is focused or not empty.
**Action:** Use CSS pseudo-classes (`:focus` and `:not(:placeholder-shown)`) combined with the adjacent sibling selector (`+`) to hide `.shortcut-hint` when the input is focused or populated, and provide the shortcut in `aria-label` for screen reader discoverability.

## 2026-06-02 - Converting Schema Columns to Native Buttons with Screen Reader Announcements
**Learning:** Emulating buttons with `<span>` requires `role="button"`, `tabindex="0"`, and custom keyboard event handlers. Using native `<button>` tags provides these for free, but requires CSS resets (`background: transparent; border: none; font-family: inherit;`) to avoid breaking the design. Additionally, injecting text into an editor is silent to screen readers unless explicitly announced via an `aria-live` region.
**Action:** Always prefer native `<button>` tags with CSS resets over emulated `<span>` buttons, and explicitly announce dynamic actions (like inserting text) to `aria-live` regions to ensure screen reader users are informed of the result.

## 2026-06-03 - Descriptive ARIA Labels for Dynamic Buttons
**Learning:** When dynamically generating action buttons that rely on visual abbreviations (like emojis, e.g., "💾 PNG") or concise text, screen reader users may lack the context to understand what the button exports or affects (especially when multiple similar buttons exist in a list of chart cards).
**Action:** Always add an explicit `aria-label` describing the full action and its target context (e.g., "Download Chart Title as PNG") and pair it with a `title` attribute for visual users who rely on tooltips, ensuring the button is intuitive for all users.
## 2024-05-16 - Accessible interactive elements and focus states
**Learning:** Native browser styles for interactive elements like `<button>` override custom layout when converted from emulated `<span>` buttons. CSS resets are strictly required (background, border, font), but `outline: none;` should explicitly be avoided to maintain default focus rings or custom `:focus-visible` states.
**Action:** Always provide explicit CSS resets (e.g., `background: transparent; border: none; font-family: inherit; font-size: inherit;`) when replacing `<span>` with `<button>`, and verify focus indicators are visually consistent.
## 2026-06-21 - Disabling Form Controls When Data is Unavailable
**Learning:** Dropdowns and actionable buttons that depend on global application state (like loaded datasets) should be explicitly disabled when that state is empty. Leaving them enabled but failing silently creates a confusing user experience.
**Action:** When adding global actions, ensure they have a function (e.g., `updateConsoleActionsUI`) that toggles their `disabled` state and `title` tooltips based on the availability of required data, and call this function during all state changes.
## 2026-06-27 - Improve schema column keyboard accessibility and feedback
**Learning:** Native `<button>` elements intrinsically support keyboard events (`click` fired by Enter/Space), negating the need for custom `keydown` handlers when converting semantic `span` buttons (like those found in data table schema representations).
**Action:** Use native `<button>` tags with CSS resets (`background: transparent; border: none;`) instead of `span` tags with `role="button"` to provide robust keyboard accessibility out-of-the-box. Add hover states to provide clear visual feedback to users that the element is interactive.
## 2026-06-28 - ARIA Live Announcements Require Dynamic Color States
**Learning:** Toast messages triggered by successful actions (like inserting a column into the query editor) must have distinct visual styling from error messages to assist sighted users, while remaining properly configured with `aria-live` for screen readers. Using a single `showToast` function with a hardcoded red color fails to convey success visually.
**Action:** When adding UX feedback toasts, ensure the toast function accepts an optional `type` parameter (e.g., 'success' vs 'error') and dynamically maps it to appropriate CSS colors (like green `#10b981` for success) so the visual experience aligns with the semantic screen reader announcement.
## 2026-06-29 - Keyboard Shortcut Discoverability
**Learning:** Global keyboard shortcuts (like `/` to search) significantly improve navigation for power users but remain undiscoverable. Adding a visual `<kbd>` hint directly within the input makes it discoverable, while using CSS `:not(:placeholder-shown)` ensures it automatically disappears when typing, keeping the UI clean without JavaScript overhead.
**Action:** Pair global keyboard shortcuts with visual `<kbd>` hints positioned absolutely over inputs, and use CSS sibling selectors with `:placeholder-shown` to manage their visibility cleanly.
## 2026-06-30 - Convert emulated buttons to native button tags
**Learning:** Using `span` elements with `role="button"` and `tabIndex="0"` is bad for accessibility as it requires manually managing keyboard events (Enter/Space) and often misses out on native screen reader benefits.
**Action:** Always prefer semantic HTML tags like `<button>` over generic container tags (`span`, `div`) with ARIA roles when creating interactive click targets, using CSS resets (`background: transparent`, `border: none`) to bypass native styling if necessary.
## 2024-07-08 - Empty State Improvements for Data Grids
**Learning:** Plain text empty states (like 'No results') lack visual hierarchy and can be confusing. Using structured HTML with a decorative `aria-hidden` icon, a bold heading, and a helpful call-to-action description provides better visual context while maintaining accessibility for screen readers.
**Action:** Always replace raw string empty states in data grids with semantic HTML structures containing hidden decorative icons and actionable helper text.
