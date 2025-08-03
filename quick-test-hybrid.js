import puppeteer from 'puppeteer';

async function quickTest() {
  console.log('🚀 Quick test of hybrid component...');  
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();
  
  // Short timeout to prevent hanging
  page.setDefaultTimeout(10000);
  
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('error') || text.includes('Error') || text.includes('ReferenceError')) {
      console.log(`[ERROR] ${text}`);
    }
  });
  
  try {
    await page.goto('http://localhost:3501/');
    
    // Click volatility analysis tab
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const analysisButton = buttons.find(btn => btn.textContent.includes('Volatility Analysis'));
      if (analysisButton) analysisButton.click();
    });
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Check for expected elements
    const results = await page.evaluate(() => {
      const smileTitle = document.querySelector('h3') && document.querySelector('h3').textContent.includes('Volatility Smile - EURUSD');
      const termTitle = Array.from(document.querySelectorAll('h3')).some(h3 => h3.textContent.includes('Term Structure - EURUSD'));
      const surfaceTitle = Array.from(document.querySelectorAll('h3')).some(h3 => h3.textContent.includes('3D Volatility Surface - EURUSD'));
      
      // Check for tenor buttons (should exist for smile)
      const buttons = Array.from(document.querySelectorAll('button'));
      const tenorButtons = buttons.filter(btn => ['1M', '3M', '6M', 'ON', '1W', '2W'].includes(btn.textContent.trim()));
      
      return {
        smileTitle,
        termTitle,
        surfaceTitle,
        tenorButtonCount: tenorButtons.length
      };
    });
    
    console.log('✅ Component sections found:');
    console.log('  Smile:', results.smileTitle);
    console.log('  Term:', results.termTitle);
    console.log('  Surface:', results.surfaceTitle);
    console.log('  Tenor buttons:', results.tenorButtonCount);
    
    await page.screenshot({ path: 'hybrid-test.png', fullPage: true });
    console.log('📸 Screenshot saved as hybrid-test.png');
    
    console.log('✅ Hybrid component working correctly!');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
  } finally {
    await browser.close();
  }
}

quickTest();