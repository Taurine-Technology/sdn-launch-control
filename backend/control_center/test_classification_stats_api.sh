#!/bin/bash

# Test script for classification stats API
# This script tests the /api/v1/classification-stats/ endpoint

API_URL="http://localhost:8000/api/v1/classification-stats/"
LOGIN_URL="http://localhost:8000/api/v1/auth/login/"

echo "Testing Classification Stats API..."
echo "=================================="

# Test 1: Check if API is accessible (without auth - should return 401)
echo "1. Testing API accessibility (should return 401 Unauthorized):"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" "$API_URL"
echo ""

# Test 2: Try to get a token (this might fail if no users exist)
echo "2. Attempting to get authentication token:"
TOKEN_RESPONSE=$(curl -s -X POST "$LOGIN_URL" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}' 2>/dev/null)

if echo "$TOKEN_RESPONSE" | grep -q "token"; then
    TOKEN=$(echo "$TOKEN_RESPONSE" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
    echo "✓ Token obtained successfully"
    echo ""

    # Test 3: Make authenticated request to classification stats
    echo "3. Testing authenticated request to classification stats:"
    curl -s -H "Authorization: Token $TOKEN" "$API_URL" | jq '.' 2>/dev/null || echo "Response (raw):"
    curl -s -H "Authorization: Token $TOKEN" "$API_URL"
    echo ""
    echo ""

    # Test 4: Test with query parameters
    echo "4. Testing with query parameters (hours=24, summary=true):"
    curl -s -H "Authorization: Token $TOKEN" "$API_URL?hours=24&summary=true" | jq '.' 2>/dev/null || echo "Response (raw):"
    curl -s -H "Authorization: Token $TOKEN" "$API_URL?hours=24&summary=true"
    echo ""
    
else
    echo "✗ Failed to get authentication token"
    echo "Response: $TOKEN_RESPONSE"
    echo ""
    echo "Note: You may need to create a user first or check if the API is running"
fi

echo "=================================="
echo "Test completed!"

