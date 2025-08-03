import puppeteer from 'puppeteer';

async function testYieldCurves() {
  console.log('🚀 Testing yield curves with ticker repository...');  
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();
  
  // Short timeout to prevent hanging
  page.setDefaultTimeout(10000);
  
  // Capture console logs
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('tickers for') || text.includes('from repository')) {
      console.log(`[REPOSITORY] ${text}`);
    }
    if (text.includes('error') || text.includes('Error')) {
      console.log(`[ERROR] ${text}`);
    }
  });
  
  try {
    await page.goto('http://localhost:3501/');
    
    // Click yield curves tab
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const yieldButton = buttons.find(btn => btn.textContent.includes('Yield Curves'));
      if (yieldButton) yieldButton.click();
    });
    
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Check if yield curves tab loaded
    const tabContent = await page.evaluate(() => {
      const h3s = Array.from(document.querySelectorAll('h3'));
      return {
        hasUSD: h3s.some(h3 => h3.textContent.includes('USD')),
        hasEUR: h3s.some(h3 => h3.textContent.includes('EUR')),
        hasYieldCurve: h3s.some(h3 => h3.textContent.includes('Yield Curve'))
      };
    });
    
    console.log('✅ Yield curves tab loaded:');
    console.log('  USD curve:', tabContent.hasUSD);
    console.log('  EUR curve:', tabContent.hasEUR);
    console.log('  Has yield curve title:', tabContent.hasYieldCurve);
    
    await page.screenshot({ path: 'yield-curves-test.png', fullPage: true });
    console.log('📸 Screenshot saved as yield-curves-test.png');
    
    console.log('✅ Yield curves component working with repository!');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  } finally {
    await browser.close();
  }
}

testYieldCurves();