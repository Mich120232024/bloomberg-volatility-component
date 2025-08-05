// Test the ticker repository service
import fs from 'fs';

// Read the JSON file directly
const jsonData = fs.readFileSync('./tools/central_bloomberg_ticker_repository_v3.json', 'utf8');
const data = JSON.parse(jsonData);

console.log('Ticker Repository Test');
console.log('=====================');
console.log('Version:', data.metadata.version);
console.log('API Endpoint:', data.metadata.api.endpoint);
console.log('\nYield Curve Data:');

// Test USD tickers
const usdData = data.yield_curve_construction.USD;
console.log('\n📊 USD Tickers:');
console.log('  Money Market:', usdData.money_market);
console.log('  Swaps:', usdData.swaps);
console.log('  Government Bonds:', usdData.government_bonds);

// Test EUR tickers
const eurData = data.yield_curve_construction.EUR;
console.log('\n📊 EUR Tickers:');
console.log('  Money Market:', eurData.money_market);
console.log('  Swaps:', eurData.swaps);
console.log('  Government Bonds:', eurData.government_bonds);

// Count total tickers
const countTickers = (curveData) => {
  let count = 0;
  if (curveData.money_market) {
    if (curveData.money_market.overnight) count += curveData.money_market.overnight.length;
    if (curveData.money_market.term) count += curveData.money_market.term.length;
  }
  if (curveData.swaps) {
    if (curveData.swaps.sofr) count += curveData.swaps.sofr.length;
    if (curveData.swaps.ois) count += curveData.swaps.ois.length;
  }
  if (curveData.government_bonds) {
    if (curveData.government_bonds.short) count += curveData.government_bonds.short.length;
    if (curveData.government_bonds.medium) count += curveData.government_bonds.medium.length;
    if (curveData.government_bonds.long) count += curveData.government_bonds.long.length;
  }
  return count;
};

console.log('\n📈 Total Tickers:');
console.log('  USD:', countTickers(usdData));
console.log('  EUR:', countTickers(eurData));