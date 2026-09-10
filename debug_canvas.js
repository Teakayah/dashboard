const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:8765/employment_rate_canada.html', { waitUntil: 'domcontentloaded' });

  const tabs = await page.locator('.tab').count();
  for (let i = 0; i < tabs; i++) {
    await page.locator('.tab').nth(i).click();
    await page.waitForTimeout(1000); // Wait a bit for rendering

    const elements = await page.evaluate(() => {
        const activePanel = document.querySelector('.panel.active');
        const container = activePanel || document.body;
        const canvases = container.querySelectorAll('canvas');

        const results = [];
        canvases.forEach(c => {
            results.push({ id: c.id, h: c.offsetHeight, w: c.offsetWidth, display: window.getComputedStyle(c).display, offsetParent: c.offsetParent !== null });
        });
        return results;
    });

    console.log(`Tab ${i} canvases:`, elements);
  }

  await browser.close();
})();
