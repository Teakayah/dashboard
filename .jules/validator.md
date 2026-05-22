## 2024-05-22 - Cover parse_args in generate_index.py
Coverage Gap: `parse_args` in `deployment/generate_index.py` was not tested, especially the argument choices.
Learning: The prompt mentioned `--responsive`, but the codebase actually had `--responsive-preset` with choices from `RESPONSIVE_PRESETS`. Always verify the actual codebase state instead of blindly following outdated prompt snippets. Also, I needed to install pytest properly before running it.
Assertion: Tested default, specific choice (`'none'`), and invalid choice for `parse_args` properly handling `SystemExit`.
