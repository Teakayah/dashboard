## 2026-05-02 - Custom Drop Zones Require Manual Keyboard Support
**Learning:** When building custom file drop zones using `div` elements, they lack native keyboard interactivity. Even if they accept click events, screen reader and keyboard-only users cannot focus or activate them without explicit `tabindex`, `role="button"`, and manual `keydown` event listeners for 'Enter' and 'Space' keys.
**Action:** Always ensure custom interactive areas meant to act like buttons have `tabindex="0"`, `role="button"`, clear `:focus-visible` styles, and keyboard event handlers that trigger the same functionality as their click events.
## 2026-05-04 - ARIA Labels for Icon-Only and Contextual Form Elements
**Learning:** In accessibility-focused code, always ensure that form elements (like `<input>` and `<select>`) have an explicit `aria-label` when a visible label is missing or when the context isn't implicitly clear to screen readers (e.g., search bars, icon-only buttons, or complex form structures like join assistants).
**Action:** When auditing forms, specifically look for `<input type="search">`, `<select>`, and `<textarea>` elements without associated `<label>` tags and add `aria-label` attributes describing their purpose.
## 2026-05-15 - Interactive Elements Hidden by Opacity Require Focus Visibility
**Learning:** Interactive elements (like the fullscreen button) that are hidden via `opacity: 0` until hovered are inaccessible to keyboard-only users who cannot "hover" to see them when they tab to the element.
**Action:** Always add a `:focus-visible` selector that sets `opacity: 1` and a clear outline when relying on hover states to reveal interactive controls.
