1. **Fix the smoke test in `test_refresh.py`**
   - Use `BeautifulSoup` to parse `index.html` after calling `module.main()`.
   - Find all `<script>` tags that have `integrity` attributes.
   - For each tag, calculate the sha256 of the source file and make sure it matches the integrity string.
   - Use `replace_with_git_merge_diff` to replace the dummy smoke test with this robust one.
2. **Remove `plan2.md`**
3. **Execute pre-commit instructions**
   - Run tests again, check coverage, verify there's no flake with `--count=5`.
4. **Submit PR**
   - Submit the PR as the Inspector persona.
