## 2024-09-17 - Remove Redundant aria-disabled
**Learning:** Native HTML elements like `<button>` automatically communicate their `disabled` state to the accessibility tree. Adding `aria-disabled` alongside the native `disabled` attribute is an anti-pattern, redundant, and can cause bugs if they fall out of sync.
**Action:** Do not explicitly manage `aria-disabled` on elements that natively support `disabled`.
