import fs from 'fs';
const data = JSON.parse(fs.readFileSync('./tools/central_bloomberg_ticker_repository_v3.json', 'utf8'));

console.log('🌍 ALL AVAILABLE YIELD CURVES IN REPOSITORY');
console.log('===========================================\n');

for (const [currency, config] of Object.entries(data.yield_curve_construction)) {
  console.log(`\n📊 ${currency} YIELD CURVE`);
  console.log('─'.repeat(40));
  
  // Money Market
  if (config.money_market) {
    console.log('\n💰 Money Market:');
    if (config.money_market.overnight) {
      console.log('  Overnight:', config.money_market.overnight.join(', '));
    }
    if (config.money_market.term) {
      console.log('  Term rates:', config.money_market.term.join(', '));
    }
    if (config.money_market.reference_rate) {
      console.log('  Reference rate:', config.money_market.reference_rate);
    }
  }
  
  // Swaps
  if (config.swaps) {
    console.log('\n📈 Swaps:');
    if (config.swaps.ois) {
      console.log('  ✅ OIS:', config.swaps.ois.join(', '));
    }
    if (config.swaps.sofr) {
      console.log('  SOFR:', config.swaps.sofr.join(', '));
    }
    if (config.swaps.sonia) {
      console.log('  SONIA:', config.swaps.sonia.join(', '));
    }
    if (config.swaps.tonar) {
      console.log('  TONAR:', config.swaps.tonar.join(', '));
    }
    if (config.swaps.saron) {
      console.log('  SARON:', config.swaps.saron.join(', '));
    }
  }
  
  // Government Bonds
  if (config.government_bonds) {
    console.log('\n🏛️ Government Bonds:');
    if (config.government_bonds.short) {
      console.log('  Short:', config.government_bonds.short.join(', '));
    }
    if (config.government_bonds.medium) {
      console.log('  Medium:', config.government_bonds.medium.join(', '));
    }
    if (config.government_bonds.long) {
      console.log('  Long:', config.government_bonds.long.join(', '));
    }
    if (config.government_bonds.germany) {
      console.log('  🇩🇪 Germany:', config.government_bonds.germany.join(', '));
    }
    if (config.government_bonds.france) {
      console.log('  🇫🇷 France:', config.government_bonds.france.join(', '));
    }
    if (config.government_bonds.uk) {
      console.log('  🇬🇧 UK:', config.government_bonds.uk.join(', '));
    }
    if (config.government_bonds.jgb) {
      console.log('  🇯🇵 JGB:', config.government_bonds.jgb.join(', '));
    }
    if (config.government_bonds.swiss) {
      console.log('  🇨🇭 Swiss:', config.government_bonds.swiss.join(', '));
    }
  }
  
  // Count total instruments
  let total = 0;
  if (config.money_market) {
    total += (config.money_market.overnight?.length || 0) + (config.money_market.term?.length || 0);
  }
  if (config.swaps) {
    total += (config.swaps.ois?.length || 0) + (config.swaps.sofr?.length || 0) + 
             (config.swaps.sonia?.length || 0) + (config.swaps.tonar?.length || 0) + 
             (config.swaps.saron?.length || 0);
  }
  if (config.government_bonds) {
    total += (config.government_bonds.short?.length || 0) + 
             (config.government_bonds.medium?.length || 0) + 
             (config.government_bonds.long?.length || 0) +
             (config.government_bonds.germany?.length || 0) +
             (config.government_bonds.france?.length || 0) +
             (config.government_bonds.uk?.length || 0) +
             (config.government_bonds.jgb?.length || 0) +
             (config.government_bonds.swiss?.length || 0);
  }
  
  console.log(`\n📊 Total instruments: ${total}`);
}

// Summary
const currencies = Object.keys(data.yield_curve_construction);
console.log('\n\n📈 SUMMARY');
console.log('─'.repeat(40));
console.log(`Total currencies with yield curves: ${currencies.length}`);
console.log(`Currencies: ${currencies.join(', ')}`);