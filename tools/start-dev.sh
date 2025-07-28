#!/bin/bash
# Start Bloomberg Gateway for local development
# NO CACHE - Always fresh Bloomberg data

echo "Starting Bloomberg Gateway (Development Mode - No Cache)"
echo "=================================================="
echo "Gateway URL: http://localhost:8000"
echo "Bloomberg VM: http://20.172.249.92:8080"
echo "Cache: DISABLED (always fresh data)"
echo ""

# Set environment variables
export ENABLE_CACHE=false
export BLOOMBERG_API_URL="http://20.172.249.92:8080"
export LOG_LEVEL=INFO

# Run the gateway
python3 bloomberg-gateway-enhanced.py