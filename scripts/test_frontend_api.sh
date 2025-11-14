#!/bin/bash
# Test script to verify frontend can connect to backend API

set -e

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
echo "Testing backend API at: $BACKEND_URL"
echo ""

# Test 1: Document Templates
echo "1. Testing GET /api/document-templates..."
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$BACKEND_URL/api/document-templates")
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" = "200" ]; then
    DOC_COUNT=$(echo "$BODY" | jq '.documents | length' 2>/dev/null || echo "0")
    echo "   ✅ Success! Found $DOC_COUNT documents"
else
    echo "   ❌ Failed with status: $HTTP_STATUS"
    echo "   Response: $BODY"
fi
echo ""

# Test 2: Create Project
echo "2. Testing POST /api/projects..."
PROJECT_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"user_idea":"Test project","selected_documents":["requirements","project_charter"]}' \
    "$BACKEND_URL/api/projects")
PROJECT_HTTP_STATUS=$(echo "$PROJECT_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
PROJECT_BODY=$(echo "$PROJECT_RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$PROJECT_HTTP_STATUS" = "202" ] || [ "$PROJECT_HTTP_STATUS" = "200" ]; then
    PROJECT_ID=$(echo "$PROJECT_BODY" | jq -r '.project_id' 2>/dev/null || echo "unknown")
    echo "   ✅ Success! Created project: $PROJECT_ID"
    
    # Test 3: Project Status
    echo ""
    echo "3. Testing GET /api/projects/$PROJECT_ID/status..."
    sleep 1
    STATUS_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$BACKEND_URL/api/projects/$PROJECT_ID/status")
    STATUS_HTTP_STATUS=$(echo "$STATUS_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
    STATUS_BODY=$(echo "$STATUS_RESPONSE" | sed '/HTTP_STATUS/d')
    
    if [ "$STATUS_HTTP_STATUS" = "200" ]; then
        STATUS=$(echo "$STATUS_BODY" | jq -r '.status' 2>/dev/null || echo "unknown")
        echo "   ✅ Success! Project status: $STATUS"
    else
        echo "   ❌ Failed with status: $STATUS_HTTP_STATUS"
    fi
else
    echo "   ❌ Failed with status: $PROJECT_HTTP_STATUS"
    echo "   Response: $PROJECT_BODY"
fi
echo ""

# Test 4: CORS Headers
echo "4. Testing CORS headers..."
CORS_RESPONSE=$(curl -s -I -H "Origin: http://localhost:3000" "$BACKEND_URL/api/document-templates")
if echo "$CORS_RESPONSE" | grep -q "Access-Control-Allow-Origin"; then
    echo "   ✅ CORS headers present"
    echo "$CORS_RESPONSE" | grep -i "access-control"
else
    echo "   ⚠️  CORS headers not found"
fi

echo ""
echo "✅ All API tests completed!"

