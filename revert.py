content = open('tests/test_accessibility.py').read()
content = content.replace("'color-contrast',  # Deferred temporarily to unblock CI due to underlying UI/CSS bugs. Tracked in Palette's scope.", "# 'color-contrast',               # Fixed via inject_contrast_fix")
open('tests/test_accessibility.py', 'w').write(content)
