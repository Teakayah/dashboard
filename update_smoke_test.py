import re

with open('tests/test_refresh.py', 'r') as f:
    content = f.read()

new_test = """
@patch("sys.argv", ["refresh.py"])
def test_smoke_test_refresh(mock_subprocess, mock_sys_exit, mock_path, monkeypatch):
    \"\"\"Smoke test that runs refresh.py end-to-end against fixture data and asserts the generated HTML has no broken <script> SRI mismatches.\"\"\"
    module = load_refresh_module()

    # Let's mock _git to simulate success
    with patch.object(module, '_git', return_value=' M index.html'):
        module.main()

    # Verify no unhandled exceptions were thrown
    mock_sys_exit.assert_not_called()

    # Check for SRI mismatches in HTML files
    import urllib.request
    import hashlib
    from bs4 import BeautifulSoup

    for html_file in module.ROOT.glob('*.html'):
        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
            for script in soup.find_all('script'):
                if script.has_attr('integrity') and script.has_attr('src') and script['src'].startswith('http'):
                    url = script['src']
                    integrity = script['integrity']

                    try:
                        with urllib.request.urlopen(url) as response:
                            content = response.read()
                            import base64
                            hash_type, hash_value = integrity.split('-', 1)
                            if hash_type == 'sha384':
                                calculated_hash = base64.b64encode(hashlib.sha384(content).digest()).decode('utf-8')
                                assert calculated_hash == hash_value, f"SRI mismatch in {html_file.name} for {url}"
                            elif hash_type == 'sha256':
                                calculated_hash = base64.b64encode(hashlib.sha256(content).digest()).decode('utf-8')
                                assert calculated_hash == hash_value, f"SRI mismatch in {html_file.name} for {url}"
                    except urllib.error.URLError:
                        pass # Ignore network errors during tests, but if it connects it must match
"""

# Replace the existing dummy test with the new test
content = re.sub(r'@patch\("sys\.argv", \["refresh\.py"\]\)\ndef test_smoke_test_refresh.*?mock_sys_exit\.assert_not_called\(\)', new_test.strip(), content, flags=re.DOTALL)

with open('tests/test_refresh.py', 'w') as f:
    f.write(content)
