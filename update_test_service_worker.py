import re

with open("tests/test_service_worker.py", "r") as f:
    content = f.read()

content = content.replace(
    "page.wait_for_timeout(1000)",
    "page.wait_for_function('''() => {\n        return caches.keys().then(keys => \n            !keys.includes('datadashboard-v1') && !keys.includes('datadashboard-v2')\n        );\n    }''')"
)

with open("tests/test_service_worker.py", "w") as f:
    f.write(content)
