// Precision test to debug 22.5bp premium discrepancy
// Expected: 1.7780%, Actual: 1.7555%, Difference: -22.5bp

// Your calculations from the UI
const spotRate = 1.08245; // EURUSD spot
const eurRate = 1.921; // EUR 1M rate
const usdRate = 4.318; // USD 1M rate
const volatility = 5.82; // ATM vol
const tenorYears = 1/12; // 1M

// Forward calculation (same as in your code)
const calculatedForward = spotRate * Math.exp((usdRate - eurRate) * tenorYears / 100);
console.log('Calculated Forward:', calculatedForward);
console.log('Forward (5 decimal):', calculatedForward.toFixed(5));

// Strike scenarios to test
const strikeScenarios = [
  { name: 'UI Strike', value: 1.183383647057844 },
  { name: 'Forward (full)', value: calculatedForward },
  { name: 'Forward (5 decimal)', value: parseFloat(calculatedForward.toFixed(5)) },
  { name: 'Forward (4 decimal)', value: parseFloat(calculatedForward.toFixed(4)) }
];

// Garman-Kohlhagen pricing function (copied from your code)
const calculateOptionPrice = (F, K, T, rDomestic, vol, optType) => {
  const rDecimal = rDomestic / 100;
  const volDecimal = vol / 100;
  
  const d1 = (Math.log(F / K) + (0.5 * volDecimal * volDecimal) * T) / (volDecimal * Math.sqrt(T));
  const d2 = d1 - volDecimal * Math.sqrt(T);
  
  // Standard normal CDF
  const normCDF = (x) => {
    const a1 =  0.254829592;
    const a2 = -0.284496736;
    const a3 =  1.421413741;
    const a4 = -1.453152027;
    const a5 =  1.061405429;
    const p  =  0.3275911;
    
    const sign = x >= 0 ? 1 : -1;
    x = Math.abs(x) / Math.sqrt(2);
    
    const t = 1.0 / (1.0 + p * x);
    const y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x);
    
    return 0.5 * (1.0 + sign * y);
  };
  
  const Nd1 = normCDF(d1);
  const Nd2 = normCDF(d2);
  
  const discountFactor = Math.exp(-rDecimal * T);
  
  let premium;
  if (optType === 'put') {
    premium = discountFactor * (K * (1 - Nd2) - F * (1 - Nd1));
  }
  
  return {
    premium: premium,
    premiumPercent: premium * 100
  };
};

console.log('\n=== PRECISION TEST RESULTS ===');
strikeScenarios.forEach(scenario => {
  const result = calculateOptionPrice(calculatedForward, scenario.value, tenorYears, usdRate, volatility, 'put');
  
  console.log(`\n${scenario.name}:`);
  console.log(`  Strike: ${scenario.value}`);
  console.log(`  F - K: ${(calculatedForward - scenario.value).toFixed(10)}`);
  console.log(`  Difference (bp): ${((calculatedForward - scenario.value) * 10000).toFixed(2)}`);
  console.log(`  Premium %: ${result.premiumPercent.toFixed(4)}%`);
  console.log(`  vs Expected (1.7780%): ${(result.premiumPercent - 1.7780).toFixed(4)}% diff`);
});