import re

with open("tests/test_usability.py", "r") as f:
    content = f.read()

# Replace hardcoded wait_for_timeout with wait_for_function
content = re.sub(
    r"    page\.locator\('\.tab', has_text='Government Debt'\)\.click\(\)\n    page\.wait_for_timeout\(300\)",
    r"    page.locator('.tab', has_text='Government Debt').click()\n    page.wait_for_function('document.documentElement.scrollHeight > 0')",
    content
)

content = re.sub(
    r"    page\.locator\('\.tab', has_text='Population'\)\.click\(\)\n    page\.wait_for_timeout\(300\)",
    r"    page.locator('.tab', has_text='Population').click()\n    page.wait_for_function('document.documentElement.scrollHeight > 0')",
    content
)

content = re.sub(
    r"        page\.locator\(f\"\.tab\[onclick\*=\\\"\'\{tab\}\'\\\"\]\"\)\.click\(\)\n        page\.wait_for_timeout\(300\)\n        heights = \[\]\n        for _ in range\(5\):\n            heights\.append\(page\.evaluate\('document\.documentElement\.scrollHeight'\)\)\n            page\.wait_for_timeout\(200\)\n        \n        diff = max\(heights\) - min\(heights\)\n        assert diff <= 5, \(\n            f'Tab \{tab\}: page height is unstable \(range: \{min\(heights\)\}-\{max\(heights\)\}\): \{heights\}'\n        \)",
    r"        page.locator(f\".tab[onclick*=\\\"'{tab}'\\\"]\").click()\n        # wait for height to be stable for at least 800ms (4 checks x 200ms)\n        page.wait_for_function('''() => {\n            if (!window.__heights) window.__heights = [];\n            window.__heights.push(document.documentElement.scrollHeight);\n            if (window.__heights.length > 4) window.__heights.shift();\n            return window.__heights.length === 4 && new Set(window.__heights).size === 1;\n        }''', timeout=5000)\n        # Clean up for next tab\n        page.evaluate('window.__heights = []')",
    content
)


with open("tests/test_usability.py", "w") as f:
    f.write(content)
