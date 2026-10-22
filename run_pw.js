const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:3000/test_batch.html');
  await page.waitForTimeout(3000);
  console.log(await page.content());
  await browser.close();
})();
