import axios from 'axios';

async function checkFullFlow() {
  try {
    console.log('Checking full volatility surface data flow...\n');
    
    // Get all securities for EURUSD
    const tenors = ["ON", "1W", "2W", "3W", "1M", "2M", "3M", "4M", "6M", "9M", "1Y", "18M", "2Y"];
    const securities = [];
    
    for (const tenor of tenors) {
      // ATM
      const atmSecurity = tenor === 'ON' ? `EURUSDV${tenor} Curncy` : `EURUSDV${tenor} BGN Curncy`;
      securities.push(atmSecurity);
      
      // Risk Reversals and Butterflies
      const deltas = [5, 10, 15, 25, 35];
      for (const delta of deltas) {
        securities.push(`EURUSD${delta}R${tenor} BGN Curncy`);
        securities.push(`EURUSD${delta}B${tenor} BGN Curncy`);
      }
    }
    
    console.log(`Total securities to fetch: ${securities.length}`);
    console.log('First 5 securities:', securities.slice(0, 5));
    
    // Fetch in chunks
    const chunkSize = 50;
    const results = [];
    
    for (let i = 0; i < securities.length; i += chunkSize) {
      const chunk = securities.slice(i, i + chunkSize);
      console.log(`\nFetching chunk ${Math.floor(i/chunkSize) + 1}/${Math.ceil(securities.length/chunkSize)} (${chunk.length} securities)...`);
      
      const response = await axios.post('http://localhost:8000/api/bloomberg/reference', {
        securities: chunk,
        fields: ["PX_BID", "PX_ASK", "PX_LAST"]
      });
      
      if (response.data.success) {
        results.push(...response.data.data.securities_data);
      }
    }
    
    // Analyze results
    console.log(`\nTotal responses: ${results.length}`);
    const successful = results.filter(r => r.success && (r.fields.PX_BID !== null || r.fields.PX_ASK !== null));
    console.log(`Successful with real Bloomberg data: ${successful.length}`);
    
    // Group by tenor
    const tenorData = {};
    for (const tenor of tenors) {
      const tenorSecurities = successful.filter(s => s.security.includes(`${tenor} `));
      if (tenorSecurities.length > 0) {
        tenorData[tenor] = tenorSecurities.length;
        console.log(`\n${tenor}: ${tenorSecurities.length} securities with real data`);
        
        // Show real Bloomberg data
        const atm = tenorSecurities.find(s => s.security.includes(`V${tenor}`));
        if (atm) {
          console.log(`  ATM: bid=${atm.fields.PX_BID}, ask=${atm.fields.PX_ASK}`);
        }
      }
    }
    
  } catch (error) {
    console.error('Error:', error.message);
  }
}

checkFullFlow();