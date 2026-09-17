## 2024-05-18 - Exception Handling Context Manager Testing
**Learning:** Testing an exception block that wraps a context manager (`with urllib.request.urlopen`) requires ensuring the exception is thrown specifically when accessing the resource (e.g. `read()` or `json.loads()`), rather than before entering the block.
**Action:** Mock the response object's methods or use a direct exception inside the context manager instead of replacing the entire outer wrapper.
