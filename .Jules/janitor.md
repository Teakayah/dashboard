## 2024-05-24 - Unused Global Variables
 Learning: standard linters like ruff may miss unused global variables, especially in config files or test utility files. Using vulture helps identify these.
 Action: Run `vulture .` periodically to find and remove truly dead global variables to reduce cognitive overhead.
