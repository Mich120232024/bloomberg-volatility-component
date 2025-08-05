/**
 * SAFE Browser Console Debug Script
 * 
 * Paste this into Chrome Console ONE FUNCTION AT A TIME
 * to avoid overwhelming the browser
 */

// 1. SAFE: Check currency buttons (paste this first)
function checkCurrencyButtons() {
    console.log('🔍 Checking currency buttons...');
    
    const buttons = Array.from(document.querySelectorAll('button'))
        .filter(btn => btn.textContent.match(/^[A-Z]{3}$/));
    
    const currencies = buttons.map(btn => btn.textContent);
    console.log(`Found ${currencies.length} currency buttons:`, currencies);
    
    return currencies;
}

// 2. SAFE: Check if chart exists (paste this second)  
function checkChart() {
    console.log('🔍 Checking for yield curve chart...');
    
    const svg = document.querySelector('svg');
    if (svg) {
        const paths = svg.querySelectorAll('path[stroke]');
        console.log(`✅ Chart found with ${paths.length} yield curves`);
    } else {
        console.log('❌ No chart found');
    }
}

// 3. SAFE: Test one currency click (paste this third)
function testOneCurrency() {
    console.log('🔍 Testing USD button click...');
    
    const usdButton = Array.from(document.querySelectorAll('button'))
        .find(btn => btn.textContent === 'USD');
    
    if (usdButton) {
        usdButton.click();
        console.log('✅ Clicked USD button');
        
        setTimeout(() => {
            const svg = document.querySelector('svg');
            if (svg) {
                console.log('✅ Chart appeared after click');
            } else {
                console.log('❌ No chart after click');
            }
        }, 2000);
    } else {
        console.log('❌ USD button not found');
    }
}

console.log('📋 SAFE DEBUG FUNCTIONS LOADED');
console.log('Run these ONE AT A TIME:');
console.log('1. checkCurrencyButtons()');
console.log('2. checkChart()'); 
console.log('3. testOneCurrency()');