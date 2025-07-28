#!/bin/bash

echo "🔍 Debugging Bloomberg API Flow"
echo "==============================="

# Debug 1: Direct Bloomberg API health check
echo -e "\n1️⃣ Checking Direct Bloomberg API Health"
python3 tools/api-test-tool.py /health --direct

# Debug 2: Through Vite proxy
echo -e "\n2️⃣ Checking Through Vite Proxy"
python3 tools/api-test-tool.py /api/health

# Debug 3: Get volatility data (direct)
echo -e "\n3️⃣ Fetching Volatility Data (Direct)"
python3 tools/api-test-tool.py /api/bloomberg/reference \
  --direct \
  -m POST \
  -d '{
    "securities": ["EURUSDVON Curncy", "EURUSDV1M BGN Curncy", "EURUSD25R1M BGN Curncy"],
    "fields": ["PX_LAST", "PX_BID", "PX_ASK"]
  }'

# Debug 4: Get volatility data (through proxy)
echo -e "\n4️⃣ Fetching Volatility Data (Through Proxy)"
python3 tools/api-test-tool.py /api/bloomberg/reference \
  -m POST \
  -d '{
    "securities": ["EURUSDVON Curncy", "EURUSDV1M BGN Curncy", "EURUSD25R1M BGN Curncy"],
    "fields": ["PX_LAST", "PX_BID", "PX_ASK"]
  }'

echo -e "\n✅ Debug complete! Check the generated JSON files for detailed responses."