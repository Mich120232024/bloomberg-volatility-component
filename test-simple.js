const axios = require('axios');

async function testSimple() {
  try {
    // Test 1: Direct API call
    console.log('Test 1: Direct API call');
    const response1 = await axios.post('http://localhost:8000/api/bloomberg/reference', {
      securities: ["EURUSDV1M BGN Curncy"],
      fields: ["PX_BID", "PX_ASK"]
    });
    console.log('Response:', JSON.stringify(response1.data, null, 2));
    
    // Test 2: Multiple securities
    console.log('\nTest 2: Multiple securities');
    const response2 = await axios.post('http://localhost:8000/api/bloomberg/reference', {
      securities: [
        "EURUSDVON BGN Curncy",
        "EURUSDV1M BGN Curncy",
        "EURUSD25R1M BGN Curncy"
      ],
      fields: ["PX_BID", "PX_ASK", "PX_LAST"]
    });
    
    if (response2.data.success) {
      console.log('Success! Securities data:');
      response2.data.data.securities_data.forEach(sec => {
        console.log(`- ${sec.security}: bid=${sec.fields.PX_BID}, ask=${sec.fields.PX_ASK}`);
      });
    }
    
  } catch (error) {
    console.error('Error:', error.message);
  }
}

testSimple();