import pytest
from pathlib import Path
from playwright.sync_api import Page
from PIL import Image, ImageChops

BASE = 'http://localhost:8765'
REPO_ROOT = Path(__file__).parent.parent
BASELINES_DIR = REPO_ROOT / 'tests' / 'baselines'
CURRENT_DIR = REPO_ROOT / 'tests' / 'current_screenshots'

def all_pages():
    pages = [p.name for p in REPO_ROOT.glob('*.html')]
    return sorted(pages)

def compare_images(img1_path, img2_path, threshold=0.01):
    img1 = Image.open(img1_path).convert('RGB')
    img2 = Image.open(img2_path).convert('RGB')
    
    if img1.size != img2.size:
        return False, f"Sizes differ: {img1.size} vs {img2.size}"
    
    diff = ImageChops.difference(img1, img2)
    
    # Calculate percentage of different pixels
    # We use a histogram to count non-zero pixels in the diff
    diff_pixels = 0
    for band in diff.split():
        diff_pixels += sum(count for i, count in enumerate(band.histogram()) if i > 0)
    
    total_pixels = img1.size[0] * img1.size[1] * 3
    diff_percent = diff_pixels / total_pixels
    
    if diff_percent > threshold:
        # Save diff for debugging
        diff_path = img2_path.parent / (img2_path.stem + "_diff.png")
        diff.save(diff_path)
        return False, f"Images differ by {diff_percent:.2%}. Diff saved to {diff_path.name}"
    return True, None

@pytest.fixture(scope="session", autouse=True)
def ensure_dirs():
    BASELINES_DIR.mkdir(parents=True, exist_ok=True)
    CURRENT_DIR.mkdir(parents=True, exist_ok=True)

@pytest.mark.parametrize('filename', all_pages())
@pytest.mark.parametrize('color_scheme', ['light', 'dark'])
def test_visual_snapshot(page: Page, filename: str, color_scheme: str):
    page.emulate_media(color_scheme=color_scheme)
    # Set a consistent viewport
    page.set_viewport_size({'width': 1280, 'height': 800})
    
    page.goto(f'{BASE}/{filename}')
    
    # Wait for network idle
    try:
        page.wait_for_load_state('networkidle', timeout=10000)
    except Exception:
        pass # Some CDN assets might be slow
    
    # Disable animations for consistency
    page.evaluate("""
        if (window.Chart) {
            Chart.defaults.animation = false;
            Object.values(Chart.instances).forEach(c => {
                if (c.options.animation !== false) {
                    c.options.animation = false;
                    c.update('none');
                }
            });
        }
    """)
    
    if filename == 'dropzone.html':
        # Wait for DuckDB Ready
        page.wait_for_function(
            "() => document.getElementById('status')?.textContent === 'DuckDB Ready'", 
            timeout=40000
        )
    
    # Extra stabilization wait
    page.wait_for_timeout(1000)
    
    snapshot_name = f"{filename.replace('.', '_')}_{color_scheme}.png"
    baseline_path = BASELINES_DIR / snapshot_name
    current_path = CURRENT_DIR / snapshot_name
    
    # Take screenshot, masking canvases which are often non-deterministic
    canvases = page.locator('canvas')
    if canvases.count() > 0:
        page.screenshot(path=str(current_path), full_page=True, mask=canvases.all())
    else:
        page.screenshot(path=str(current_path), full_page=True)
    
    if not baseline_path.exists():
        # Create baseline if missing
        if canvases.count() > 0:
            page.screenshot(path=str(baseline_path), full_page=True, mask=canvases.all())
        else:
            page.screenshot(path=str(baseline_path), full_page=True)
        pytest.skip(f"Baseline created for {snapshot_name}")
    
    # Compare
    is_same, reason = compare_images(baseline_path, current_path)
    assert is_same, f"Visual regression detected in {snapshot_name}: {reason}"
