## 2026-05-15 - Semantic Labels and Dark Mode Interactions
**Learning:** Using generic `<span>` elements adjacent to inputs reduces tap target sizes and context for screen readers. Additionally, hardcoded light backgrounds (like `#eff6ff`) for interaction states break dark-mode visibility.
**Action:** Always pair inputs with semantic `<label for="...">` elements and prefer low-opacity primary colors (e.g., `rgba(29, 78, 216, 0.1)`) over solid light hex codes for hover/drag interaction backgrounds.
