/**
 * Browser Console Debug Script for Yield Curves
 * 
 * Copy and paste this into Chrome DevTools Console while on the Yield Curves tab
 * This will test all currency configurations and API calls
 */

console.log('🚀 YIELD CURVES DEBUG TEST');
console.log('=' .repeat(50));

// Test 1: Check if YIELD_CURVE_CONFIGS is loaded
function testYieldCurveConfigs() {
    console.log('\n📍 Testing YIELD_CURVE_CONFIGS...');
    
    // Try to access the configs from the window object or React DevTools
    const configKeys = Object.keys(window.YIELD_CURVE_CONFIGS || {});
    
    if (configKeys.length > 0) {
        console.log(`✅ Found ${configKeys.length} yield curve configs:`, configKeys);
        return configKeys;
    } else {
        console.log('❌ YIELD_CURVE_CONFIGS not found in window object');
        console.log('💡 Trying to access through React component...');
        
        // Alternative: Check if component is loaded
        const buttons = document.querySelectorAll('button');
        const currencyButtons = Array.from(buttons).filter(btn => 
            btn.textContent.match(/^[A-Z]{3}$/)
        );
        
        const currencies = currencyButtons.map(btn => btn.textContent);
        console.log(`✅ Found ${currencies.length} currency buttons:`, currencies);
        return currencies;
    }
}

// Test 2: Check currency buttons in UI
function testCurrencyButtons() {
    console.log('\n📍 Testing currency buttons in UI...');
    
    const buttons = document.querySelectorAll('button');
    const currencyButtons = Array.from(buttons).filter(btn => 
        btn.textContent.match(/^[A-Z]{3}$/)  // 3-letter currency codes
    );
    
    const g10Currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD', 'NOK', 'SEK', 'NZD'];
    const emCurrencies = ['DKK', 'ISK', 'PLN', 'CZK', 'HUF', 'CNH', 'KRW', 'SGD', 'THB', 'TWD', 'INR', 'PHP', 'HKD', 'MXN', 'TRY', 'ZAR', 'RUB'];
    
    const foundCurrencies = currencyButtons.map(btn => btn.textContent);
    const foundG10 = foundCurrencies.filter(c => g10Currencies.includes(c));
    const foundEM = foundCurrencies.filter(c => emCurrencies.includes(c));
    
    console.log(`📊 CURRENCY BUTTON SUMMARY:`);
    console.log(`   Total buttons found: ${foundCurrencies.length}`);
    console.log(`   G10 found: ${foundG10.length}/10 - ${foundG10.join(', ')}`);
    console.log(`   EM found: ${foundEM.length}/17 - ${foundEM.join(', ')}`);
    console.log(`   All currencies: ${foundCurrencies.join(', ')}`);
    
    // Check if BRL and ILS are correctly excluded
    const excludedFound = foundCurrencies.filter(c => ['BRL', 'ILS'].includes(c));
    if (excludedFound.length === 0) {
        console.log('✅ BRL and ILS correctly excluded (no working tickers)');
    } else {
        console.log(`⚠️  Found excluded currencies: ${excludedFound.join(', ')}`);
    }
    
    return { total: foundCurrencies.length, g10: foundG10.length, em: foundEM.length, currencies: foundCurrencies };
}

// Test 3: Test API call by clicking a currency
async function testApiCall(currency = 'USD') {
    console.log(`\n📍 Testing API call for ${currency}...`);
    
    // Find the currency button
    const buttons = document.querySelectorAll('button');
    const currencyButton = Array.from(buttons).find(btn => btn.textContent === currency);
    
    if (!currencyButton) {
        console.log(`❌ ${currency} button not found`);
        return;
    }
    
    // Monitor network requests
    const originalFetch = window.fetch;
    let apiCalled = false;
    
    window.fetch = function(...args) {
        const url = args[0];
        if (typeof url === 'string' && url.includes('bloomberg')) {
            console.log(`🌐 API call detected: ${url}`);
            apiCalled = true;
        }
        return originalFetch.apply(this, args);
    };
    
    // Click the button
    console.log(`👆 Clicking ${currency} button...`);
    currencyButton.click();
    
    // Wait for potential API call
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Restore original fetch
    window.fetch = originalFetch;
    
    if (apiCalled) {
        console.log('✅ API call was triggered');
    } else {
        console.log('⚠️  No API call detected (may be cached or different implementation)');
    }
    
    // Check if chart appeared
    const svg = document.querySelector('svg');
    if (svg) {
        const paths = svg.querySelectorAll('path[stroke]');
        console.log(`✅ Chart rendered with ${paths.length} yield curve paths`);
    } else {
        console.log('❌ No chart (SVG) found after clicking');
    }
}

// Test 4: Check console errors
function checkConsoleErrors() {
    console.log('\n📍 Checking for console errors...');
    
    // This is a simplified check - real errors would have appeared above
    console.log('✅ Console error check complete (see above for any red errors)');
}

// Test 5: Test chart rendering
function testChartRendering() {
    console.log('\n📍 Testing chart rendering...');
    
    const svg = document.querySelector('svg');
    if (!svg) {
        console.log('❌ No SVG chart found');
        return;
    }
    
    const paths = svg.querySelectorAll('path[stroke]');
    const circles = svg.querySelectorAll('circle');
    const xAxis = svg.querySelector('g.x-axis, g[class*="axis"]');
    const yAxis = svg.querySelector('g.y-axis, g[class*="axis"]');
    
    console.log(`📊 CHART ANALYSIS:`);
    console.log(`   SVG dimensions: ${svg.getAttribute('width')}x${svg.getAttribute('height')}`);
    console.log(`   Yield curve paths: ${paths.length}`);
    console.log(`   Data points (circles): ${circles.length}`);
    console.log(`   Has axes: ${xAxis && yAxis ? 'Yes' : 'No'}`);
    
    if (paths.length > 0) {
        console.log('✅ Chart is rendering yield curves');
        
        // Check path data
        paths.forEach((path, i) => {
            const d = path.getAttribute('d');
            const stroke = path.getAttribute('stroke');
            console.log(`   Path ${i + 1}: ${d ? 'Has data' : 'No data'}, Color: ${stroke}`);
        });
    } else {
        console.log('❌ No yield curve paths found');
    }
}

// Main test runner
async function runAllTests() {
    console.log('🔄 Running all debug tests...\n');
    
    // Test 1: Configs
    const currencies = testYieldCurveConfigs();
    
    // Test 2: UI buttons
    const buttonResults = testCurrencyButtons();
    
    // Test 3: Chart rendering
    testChartRendering();
    
    // Test 4: Console errors
    checkConsoleErrors();
    
    // Test 5: API call (with a popular currency)
    if (buttonResults.currencies.includes('USD')) {
        await testApiCall('USD');
    } else if (buttonResults.currencies.length > 0) {
        await testApiCall(buttonResults.currencies[0]);
    }
    
    // Final summary
    console.log('\n📋 FINAL SUMMARY');
    console.log('=' .repeat(50));
    console.log(`✅ Currency buttons found: ${buttonResults.total}/27 expected`);
    console.log(`✅ G10 currencies: ${buttonResults.g10}/10`);
    console.log(`✅ EM currencies: ${buttonResults.em}/17`);
    
    if (buttonResults.total >= 25) {
        console.log('🎉 EXCELLENT: Nearly all currencies rendering!');
    } else if (buttonResults.total >= 20) {
        console.log('👍 GOOD: Most currencies rendering');
    } else {
        console.log('⚠️  NEEDS ATTENTION: Missing many currencies');
    }
    
    console.log('\n💡 NEXT STEPS:');
    console.log('1. Navigate to Yield Curves tab if not already there');
    console.log('2. Try clicking different currency buttons');
    console.log('3. Check Network tab for Bloomberg API calls'); 
    console.log('4. Look for any red console errors');
}

// Auto-run the tests
runAllTests();

// Expose functions for manual testing
window.debugYieldCurves = {
    testConfigs: testYieldCurveConfigs,
    testButtons: testCurrencyButtons,
    testApi: testApiCall,
    testChart: testChartRendering,
    runAll: runAllTests
};

console.log('\n💡 Functions available for manual testing:');
console.log('debugYieldCurves.testButtons() - Test currency buttons');
console.log('debugYieldCurves.testApi("EUR") - Test API call for EUR');
console.log('debugYieldCurves.testChart() - Test chart rendering');
console.log('debugYieldCurves.runAll() - Run all tests again');