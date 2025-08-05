import puppeteer from 'puppeteer';

async function takeScreenshot() {
  let browser;
  
  try {
    // Launch browser
    browser = await puppeteer.launch({
      headless: 'new',
      defaultViewport: {
        width: 1920,
        height: 1080
      }
    });
    
    const page = await browser.newPage();
    
    // Navigate to the page
    console.log('Navigating to http://localhost:3501...');
    await page.goto('http://localhost:3501', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });
    
    // Wait a bit for initial load
    await page.waitForTimeout(2000);
    
    // Look for the FX Portfolio tab and click it
    console.log('Looking for FX Portfolio tab...');
    
    // Try different selectors for the tab
    const selectors = [
      'button:has-text("FX Portfolio")',
      '[role="tab"]:has-text("FX Portfolio")',
      'a:has-text("FX Portfolio")',
      '*:has-text("FX Portfolio")',
      // More specific selectors
      'button:contains("FX Portfolio")',
      'div:contains("FX Portfolio")',
      'span:contains("FX Portfolio")'
    ];
    
    let clicked = false;
    for (const selector of selectors) {
      try {
        // Use page.evaluate to find elements containing the text
        const element = await page.evaluateHandle(() => {
          const elements = Array.from(document.querySelectorAll('*'));
          return elements.find(el => 
            el.textContent && 
            el.textContent.includes('FX Portfolio') && 
            (el.tagName === 'BUTTON' || el.tagName === 'A' || el.hasAttribute('role'))
          );
        });
        
        if (element && element.asElement()) {
          await element.asElement().click();
          clicked = true;
          console.log('Clicked on FX Portfolio tab');
          break;
        }
      } catch (e) {
        // Try next selector
      }
    }
    
    // If standard selectors didn't work, try XPath
    if (!clicked) {
      try {
        const [element] = await page.$x("//*[contains(text(), 'FX Portfolio')]");
        if (element) {
          await element.click();
          clicked = true;
          console.log('Clicked on FX Portfolio tab using XPath');
        }
      } catch (e) {
        console.log('Could not find FX Portfolio tab with XPath');
      }
    }
    
    if (!clicked) {
      console.log('Warning: Could not find FX Portfolio tab, taking screenshot of current state');
    }
    
    // Wait for any animations or data loading
    await page.waitForTimeout(3000);
    
    // Take screenshot
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `fx-portfolio-screenshot-${timestamp}.png`;
    
    await page.screenshot({
      path: filename,
      fullPage: false
    });
    
    console.log(`Screenshot saved as: ${filename}`);
    
  } catch (error) {
    console.error('Error:', error.message);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// Run the screenshot function
takeScreenshot();