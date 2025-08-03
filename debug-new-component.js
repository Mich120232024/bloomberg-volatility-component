import puppeteer from 'puppeteer';

async function quickTest() {
  console.log('🚀 Quick test of new component...');  
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();
  
  page.on('console', msg => console.log(`[BROWSER] ${msg.text()}`));
  
  await page.goto('http://localhost:3501/');
  await page.waitForTimeout(3000);
  
  // Click volatility analysis  
  await page.click('text=Volatility Analysis');
  await page.waitForTimeout(5000);
  
  // Look for new component console logs
  const hasNewLogs = await page.evaluate(() => {
    return window.console.logs?.some(log => log.includes('🚀 Fetching data for'));
  });
  
  console.log('New component logs detected:', hasNewLogs);
  
  // Check for section titles  
  const smileExists = await page.$('text=Volatility Smile - EURUSD');
  const termExists = await page.$('text=Term Structure - EURUSD'); 
  const surfaceExists = await page.$('text=3D Volatility Surface - EURUSD');
  
  console.log('Component sections:');
  console.log('  Smile:', !!smileExists);
  console.log('  Term:', !!termExists);
  console.log('  Surface:', !!surfaceExists);
  
  await page.screenshot({ path: 'quick-test.png', fullPage: true });
  console.log('Screenshot saved as quick-test.png');
  
  console.log('Browser left open for inspection');
}

quickTest().catch(console.error);