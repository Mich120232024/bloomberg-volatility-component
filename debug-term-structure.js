import puppeteer from 'puppeteer';

async function debugTermStructure() {
  console.log('🚀 Starting Puppeteer debug session...');
  
  const browser = await puppeteer.launch({ 
    headless: false,
    devtools: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  // Listen for console logs
  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    console.log(`[BROWSER ${type.toUpperCase()}] ${text}`);
  });
  
  // Listen for network requests
  page.on('response', response => {
    const url = response.url();
    if (url.includes('/api/bloomberg')) {
      console.log(`[NETWORK] ${response.status()} - ${url}`);
    }
  });
  
  // Navigate to the app
  console.log('📱 Navigating to app...');
  await page.goto('http://localhost:3501/', { waitUntil: 'networkidle0' });
  
  // Wait for the app to load
  await page.waitForTimeout(2000);
  
  // Force refresh to ensure new component loads
  console.log('🔄 Refreshing page to load new component...');
  await page.reload({ waitUntil: 'networkidle0' });
  await page.waitForTimeout(2000);
  
  // Click on Volatility Analysis tab
  console.log('🎯 Clicking Volatility Analysis tab...');
  try {
    await page.click('text=Volatility Analysis');
  } catch (e) {
    console.log('Trying alternative selector...');
    await page.click('[role="button"]:has-text("Volatility Analysis")');
  }
  
  // Wait for content to load
  await page.waitForTimeout(5000);
  
  // Check components
  console.log('🔍 Checking component structure...');
  
  // Look for the new component
  const smileSection = await page.$('text=Volatility Smile - EURUSD');
  const termSection = await page.$('text=Term Structure - EURUSD');
  const surfaceSection = await page.$('text=3D Volatility Surface - EURUSD');
  
  console.log('📊 Component sections found:');
  console.log('  - Volatility Smile:', !!smileSection);
  console.log('  - Term Structure:', !!termSection);
  console.log('  - 3D Surface:', !!surfaceSection);
  
  // Check for chart elements
  const svgElements = await page.$$('svg');
  console.log('📈 SVG elements found:', svgElements.length);
  
  // Check for any error messages
  const errorElements = await page.$$eval('*', elements => 
    elements.filter(el => 
      el.textContent && 
      /error|Error|failed|Failed|No data|not available/i.test(el.textContent)
    ).map(el => el.textContent)
  );
  
  if (errorElements.length > 0) {
    console.log('❌ Found error/no-data messages:');
    errorElements.forEach((text, i) => console.log(`   ${i + 1}: ${text}`));
  }
  
  // Check for loading states
  const loadingElements = await page.$$eval('*', elements => 
    elements.filter(el => 
      el.textContent && 
      /loading|Loading|Fetching/i.test(el.textContent)
    ).map(el => el.textContent)
  );
  
  if (loadingElements.length > 0) {
    console.log('⏳ Found loading states:');
    loadingElements.forEach((text, i) => console.log(`   ${i + 1}: ${text}`));
  }
  
  // Wait a bit more and check again
  console.log('⏰ Waiting 5 more seconds for data...');
  await page.waitForTimeout(5000);
  
  // Take a screenshot
  await page.screenshot({ path: 'new-component-debug.png', fullPage: true });
  console.log('📸 Screenshot saved as new-component-debug.png');
  
  // Check final state
  const finalSvgCount = await page.$$('svg');
  console.log('📊 Final SVG count:', finalSvgCount.length);
  
  console.log('🔍 Browser left open for manual inspection. Close when done.');
  
  // Don't close browser automatically - let user inspect
  // await browser.close();
}

debugTermStructure().catch(console.error);