import pytest
import subprocess
import os
from pathlib import Path

def test_refresh_end_to_end_sri(page):
    root_dir = Path(__file__).parent.parent

    # Run the refresh script with flags to skip some steps for a smoke test
    result = subprocess.run(
        ["python3", "deployment/refresh.py", "--no-push", "--no-descriptions"],
        cwd=str(root_dir),
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, f"Refresh script failed: {result.stderr}\n{result.stdout}"

    html_files = list(root_dir.glob("*.html"))
    assert len(html_files) > 0, "No HTML files found"

    for html_file in html_files:
        if "dropzone.html" in html_file.name:
            continue # Skip dropzone for now, it's tested elsewhere

        sri_errors = []

        def handle_console(msg):
            if msg.type == "error" and ("Subresource Integrity" in msg.text or "Failed to find a valid digest" in msg.text):
                sri_errors.append(msg.text)

        page.on("console", handle_console)

        # Use file:// protocol to load the local file
        file_url = f"file://{html_file.resolve()}"
        page.goto(file_url, wait_until="networkidle")

        # Unsubscribe to avoid duplicates for the next file
        page.remove_listener("console", handle_console)

        assert len(sri_errors) == 0, f"SRI error found in {html_file.name}: {sri_errors}"
