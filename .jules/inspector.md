## 2024-05-24 - Exception handling in file reads
**Learning:** File reading with json.loads and read_text inside a broad try/except block needs specific mocks to guarantee coverage of the except path without writing temporary files.
**Action:** When testing exception handling for file reads combined with JSON parsing, mock read_text directly to throw an exception to cleanly test the exception handler.
