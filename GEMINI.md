# Project Instructions

## Git Workflow & Merge Strategy

This project follows an **Integration Branch Strategy (Dev-to-Main)** to manage the high volume of automated agent contributions and generated UI artifacts.

### 1. Branching Model
- **`main`**: Production-ready code and latest generated assets (HTML, previews). No direct commits allowed except by CI.
- **`dev`**: Integration branch for all features and agent PRs.
- **Feature/Agent Branches**: All new work (human or bot) MUST branch from and target `dev`.

### 2. Merging into `dev`
- Always use **Squash and Merge** when merging feature/agent branches into `dev`.
- This keeps the integration history clean and allows for easy reversion of automated changes if needed.

### 3. Handling Generated Assets
- **DO NOT commit generated files** (`index.html`, `feed.xml`, `previews/`, root `*.html` files) to feature or agent branches.
- The CI pipeline on the `dev` branch is responsible for:
    1. Running usability tests.
    2. Auto-merging `dev` into `main`.
    3. Re-generating all artifacts and committing them directly to `main`.

### 4. Continuous Integration
The `.github/workflows/ci-automerge.yml` pipeline handles the safe promotion of code from `dev` to `main`, including intelligent conflict resolution for generated files.
