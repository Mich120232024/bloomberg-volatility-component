import puppeteer from 'puppeteer';

async function testLiveYields() {
  console.log('🚀 Testing live yield curve values...');  
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();
  
  page.setDefaultTimeout(15000);
  
  // Capture console logs and network responses
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('Bloomberg response') || text.includes('rate') || text.includes('%')) {
      console.log(`[DATA] ${text}`);
    }
  });
  
  page.on('response', async response => {
    if (response.url().includes('bloomberg/reference')) {
      try {
        const data = await response.json();
        console.log('[API RESPONSE]:', JSON.stringify(data, null, 2).substring(0, 500));
      } catch (e) {}
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
    
    console.log('⏳ Waiting for data to load...');
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // Check what's displayed
    const curveInfo = await page.evaluate(() => {
      const title = document.querySelector('h3')?.textContent;
      const loading = document.body.textContent.includes('Loading');
      const hasChart = document.querySelector('svg') !== null;
      const currencies = Array.from(document.querySelectorAll('button'))
        .filter(btn => ['USD', 'EUR', 'GBP', 'JPY', 'CHF'].includes(btn.textContent))
        .map(btn => ({
          currency: btn.textContent,
          selected: btn.style.backgroundColor !== '' && !btn.style.backgroundColor.includes('transparent')
        }));
      
      return { title, loading, hasChart, currencies };
    });
    
    console.log('\n📊 Yield Curve Status:');
    console.log('  Title:', curveInfo.title);
    console.log('  Loading:', curveInfo.loading);
    console.log('  Has Chart:', curveInfo.hasChart);
    console.log('  Currencies:', curveInfo.currencies);
    
    await page.screenshot({ path: 'live-yields-test.png', fullPage: true });
    console.log('\n📸 Screenshot saved as live-yields-test.png');
    
    // Keep browser open to see values
    console.log('\n✅ Browser left open for inspection');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    await browser.close();
  }
}

testLiveYields();