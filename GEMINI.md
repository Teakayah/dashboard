# Project Instructions

## Git Workflow & Merge Strategy

This project follows an **Integration Branch Strategy (Integration-to-Main)** to manage the high volume of automated agent contributions and generated UI artifacts.

### 1. Branching Model
- **`main`**: Production-ready code and latest generated assets (HTML, previews). No direct commits allowed except by CI.
- **`integration`**: Integration branch for all features and agent PRs.
- **Feature/Agent Branches**: All new work (human or bot) MUST branch from and target `integration`.

### 2. Merging into `integration`
- Always use **Squash and Merge** when merging feature/agent branches into `integration`.
- This keeps the integration history clean and allows for easy reversion of automated changes if needed.

### 3. Handling Generated Assets
- **DO NOT commit generated files** (`index.html`, `feed.xml`, `previews/`, root `*.html` files) to feature or agent branches.
- The CI pipeline is triggered by a **Pull Request from `integration` to `main`**.
- Upon opening/updating the PR, the CI:
    1. Runs usability tests.
    2. Auto-merges `integration` into `main`.
    3. Re-generates all artifacts and commits them directly to `main`.

### 4. Continuous Integration
The `.github/workflows/ci-automerge.yml` pipeline handles the safe promotion of code from `integration` to `main` on-demand via Pull Requests, saving on CI tasks by not running on every intermediate push.

