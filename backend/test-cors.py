#!/usr/bin/env python3
"""
Quick CORS test script
Run this to verify CORS is working correctly
"""

import requests
import json

def test_cors():
    """Test CORS configuration"""
    
    backend_url = "http://localhost:8000"
    
    print("🧪 Testing CORS Configuration")
    print("=" * 50)
    
    # Test 1: OPTIONS request (preflight)
    print("\n1️⃣  Testing OPTIONS (Preflight) Request...")
    try:
        response = requests.options(
            f"{backend_url}/api/claims/submit",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Headers:")
        for header, value in response.headers.items():
            if "access-control" in header.lower():
                print(f"     {header}: {value}")
        
        if "access-control-allow-origin" in response.headers:
            print("   ✅ CORS preflight working!")
        else:
            print("   ⚠️  CORS headers not found in preflight")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Actual POST request
    print("\n2️⃣  Testing POST Request with Origin...")
    try:
        response = requests.post(
            f"{backend_url}/api/claims/submit",
            headers={
                "Origin": "http://localhost:3000",
                "Content-Type": "application/json"
            },
            json={
                "policy_number": "POL-TEST-CORS",
                "claim_type": "auto",
                "claim_amount": 1000.0,
                "incident_date": "2025-11-15",
                "description": "Test claim for CORS verification",
                "claimant_name": "CORS Test",
                "claimant_email": "cors@test.com",
                "documents": []
            }
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   CORS Headers:")
        for header, value in response.headers.items():
            if "access-control" in header.lower():
                print(f"     {header}: {value}")
        
        if response.status_code == 200:
            print("   ✅ POST request successful!")
            print(f"   Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"   ⚠️  Status: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Health check
    print("\n3️⃣  Testing Health Endpoint...")
    try:
        response = requests.get(f"{backend_url}/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Backend is healthy!")
            print(f"   Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Backend not running: {e}")
        print("   Make sure backend is started: uvicorn main:app --reload")
    
    print("\n" + "=" * 50)
    print("✅ CORS Test Complete!")
    print("\nIf you see CORS errors:")
    print("  1. Check backend is running")
    print("  2. Verify CORS_ORIGINS in .env includes your frontend URL")
    print("  3. Restart backend after changing .env")
    print("  4. Check browser console for detailed error messages")

if __name__ == "__main__":
    test_cors()

