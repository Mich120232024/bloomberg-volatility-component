#!/usr/bin/env python3
"""
FastAPI Testing Tool - Call any local API endpoint easily
"""

import json
import sys
import argparse
import requests
from typing import Dict, Any, Optional
from datetime import datetime

class APITestTool:
    def __init__(self, base_url: str = "http://localhost:3501"):
        self.base_url = base_url
        self.session = requests.Session()
        # Default headers for Bloomberg API
        self.session.headers.update({
            'Authorization': 'Bearer test',
            'Content-Type': 'application/json'
        })
    
    def call(self, 
             endpoint: str, 
             method: str = "GET", 
             data: Optional[Dict[str, Any]] = None,
             params: Optional[Dict[str, Any]] = None,
             headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Call any API endpoint with specified method and data"""
        
        url = f"{self.base_url}{endpoint}"
        
        # Override headers if provided
        req_headers = self.session.headers.copy()
        if headers:
            req_headers.update(headers)
        
        print(f"\n🔍 {method} {url}")
        if data:
            print(f"📤 Body: {json.dumps(data, indent=2)}")
        if params:
            print(f"❓ Params: {params}")
        print(f"📋 Headers: {dict(req_headers)}")
        print("-" * 50)
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=req_headers,
                timeout=30
            )
            
            print(f"✅ Status: {response.status_code}")
            
            try:
                result = response.json()
                print(f"📥 Response: {json.dumps(result, indent=2)}")
                return result
            except json.JSONDecodeError:
                print(f"📥 Response (text): {response.text}")
                return {"text": response.text, "status": response.status_code}
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {str(e)}")
            return {"error": str(e)}

def main():
    parser = argparse.ArgumentParser(description='FastAPI Testing Tool')
    parser.add_argument('endpoint', help='API endpoint (e.g., /api/bloomberg/reference)')
    parser.add_argument('-m', '--method', default='GET', help='HTTP method (GET, POST, PUT, DELETE)')
    parser.add_argument('-d', '--data', help='JSON data for request body')
    parser.add_argument('-p', '--params', help='Query parameters as JSON')
    parser.add_argument('-H', '--headers', help='Additional headers as JSON')
    parser.add_argument('-b', '--base-url', default='http://localhost:3501', help='Base URL')
    parser.add_argument('--direct', action='store_true', help='Use direct Bloomberg URL (20.172.249.92:8080)')
    
    args = parser.parse_args()
    
    # Use direct Bloomberg URL if specified
    base_url = 'http://20.172.249.92:8080' if args.direct else args.base_url
    
    tool = APITestTool(base_url)
    
    # Parse JSON data
    data = json.loads(args.data) if args.data else None
    params = json.loads(args.params) if args.params else None
    headers = json.loads(args.headers) if args.headers else None
    
    # Make the API call
    result = tool.call(
        endpoint=args.endpoint,
        method=args.method.upper(),
        data=data,
        params=params,
        headers=headers
    )
    
    # Save to file for analysis
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"api_response_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump({
            'request': {
                'endpoint': args.endpoint,
                'method': args.method,
                'data': data,
                'params': params,
                'headers': headers,
                'base_url': base_url
            },
            'response': result,
            'timestamp': timestamp
        }, f, indent=2)
    
    print(f"\n💾 Response saved to: {filename}")

if __name__ == "__main__":
    main()