import puppeteer from 'puppeteer';

async function testHybrid() {
  console.log('🚀 Testing hybrid component...');  
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();
  
  page.on('console', msg => console.log(`[BROWSER] ${msg.text()}`));
  page.on('error', err => console.error(`[PAGE ERROR] ${err.message}`));
  
  await page.goto('http://localhost:3501/');
  await page.waitForTimeout(3000);
  
  // Click volatility analysis tab
  await page.click('button:has-text("Volatility Analysis")');
  await page.waitForTimeout(5000);
  
  // Check for expected elements
  const smileTitle = await page.$('h3:has-text("Volatility Smile - EURUSD")');
  const termTitle = await page.$('h3:has-text("Term Structure - EURUSD")'); 
  const surfaceTitle = await page.$('h3:has-text("3D Volatility Surface - EURUSD")');
  
  console.log('Component sections found:');
  console.log('  Smile:', !!smileTitle);
  console.log('  Term:', !!termTitle);
  console.log('  Surface:', !!surfaceTitle);
  
  // Check for tenor buttons (should exist for smile)
  const tenorButtons = await page.$$('button:has-text("1M"), button:has-text("3M"), button:has-text("6M")');
  console.log('  Tenor buttons:', tenorButtons.length);
  
  // Check that delta buttons DON'T exist for term structure  
  const deltaButtons = await page.$$('button:has-text("10Δ"), button:has-text("25Δ"), button:has-text("ATM")');
  console.log('  Delta buttons (should be 0):', deltaButtons.length);
  
  await page.screenshot({ path: 'hybrid-test.png', fullPage: true });
  console.log('Screenshot saved as hybrid-test.png');
  
  console.log('Browser left open for inspection');
}

testHybrid().catch(console.error);