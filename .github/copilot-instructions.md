# Repository instructions

## Branching and generated files

- Feature branches target `integration`; `integration` is promoted to `main` through a reviewed pull request.
- `main` is the deployed branch. Generated artifacts belong on `main` only.
- Do not commit generated root HTML pages, `index.html`, `feed.xml`, `previews/`, `favicon.ico`, or `descriptions.json` to feature branches or `integration`. Edit their source files and let the deployment workflow regenerate them.
- `dropzone.html` is source and may be changed on feature branches.

## Accessibility and user-facing behavior

- Body text must meet WCAG AA contrast: at least 4.5:1.
- Do not use `alert()` in user flows; provide accessible inline status or error messages instead.
