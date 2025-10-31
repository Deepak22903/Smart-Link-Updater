#!/bin/bash

# Test All SmartLink API Endpoints
# Run this script to verify all endpoints are working before deployment

BASE_URL="${1:-http://localhost:8000}"
echo "Testing endpoints at: $BASE_URL"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Helper function to test endpoint
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    local expected_status=${5:-200}
    
    echo -n "Testing $name... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    elif [ "$method" = "PUT" ]; then
        response=$(curl -s -w "\n%{http_code}" -X PUT "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $http_code)"
        ((PASSED++))
        if [ -n "$body" ] && command -v jq &> /dev/null; then
            echo "$body" | jq -C '.' 2>/dev/null || echo "$body"
        else
            echo "$body"
        fi
    else
        echo -e "${RED}✗ FAILED${NC} (Expected $expected_status, got $http_code)"
        ((FAILED++))
        echo "$body"
    fi
    echo ""
}

# 1. Test Extractors List
test_endpoint "List extractors" "GET" "/api/extractors/list" "" 200

# 2. Test Posts List (detailed with health)
test_endpoint "List posts (detailed)" "GET" "/api/posts/list" "" 200

# 3. Test specific post config (if post 105 exists)
test_endpoint "Get post config (105)" "GET" "/config/post/105" "" 200

# 4. Test configured sites
test_endpoint "List configured sites" "GET" "/config/sites" "" 200

# 5. Test Batch Update (async mode)
echo -e "${YELLOW}Testing batch update (async)...${NC}"
batch_response=$(curl -s -X POST "$BASE_URL/api/batch-update" \
    -H "Content-Type: application/json" \
    -d '{"post_ids": [105], "sync": false, "initiator": "test_script", "target": "this"}')

request_id=$(echo "$batch_response" | jq -r '.request_id')

if [ "$request_id" != "null" ] && [ -n "$request_id" ]; then
    echo -e "${GREEN}✓ Batch created${NC}"
    echo "$batch_response" | jq -C '.'
    ((PASSED++))
    
    # Wait for batch to complete
    echo ""
    echo "Waiting for batch to complete..."
    sleep 5
    
    # 6. Test Batch Status
    test_endpoint "Get batch status" "GET" "/api/batch-status/$request_id" "" 200
    
    # 7. Test Batch Logs
    test_endpoint "Get batch logs (post 105)" "GET" "/api/batch-logs/$request_id/105" "" 200
    
else
    echo -e "${RED}✗ Failed to create batch${NC}"
    echo "$batch_response"
    ((FAILED++))
fi

# 8. Test Update Post Config (optional - uncomment to test)
# test_endpoint "Update post config" "PUT" "/api/posts/999/config" \
#     '{"source_urls": ["https://example.com"], "timezone": "Asia/Kolkata"}' 200

echo ""
echo "=================================="
echo "Test Summary:"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo "=================================="

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed! ✗${NC}"
    exit 1
fi
