#!/bin/bash

# Test commands for AI Assistant API
# Replace YOUR_JWT_TOKEN with an actual Supabase JWT token

echo "================================================"
echo "AI Assistant API Test Commands"
echo "================================================"
echo ""
echo "1. Test without authentication (should return 401 or 403):"
echo ""
curl -X POST http://localhost:8000/api/v1/ai-assistant/chat/send/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello AI"}' \
  -w "\nStatus: %{http_code}\n"

echo ""
echo "================================================"
echo "2. Test with authentication (replace YOUR_JWT_TOKEN):"
echo ""
echo "First, get a token from Supabase (example using their API):"
echo ""
echo 'curl -X POST https://YOUR_PROJECT.supabase.co/auth/v1/token?grant_type=password \'
echo '  -H "Content-Type: application/json" \'
echo '  -H "apikey: YOUR_SUPABASE_ANON_KEY" \'
echo '  -d '\''{"email": "test@example.com", "password": "yourpassword"}'\'''

echo ""
echo "================================================"
echo "3. Then use the token to call AI Assistant:"
echo ""
echo 'curl -X POST http://localhost:8000/api/v1/ai-assistant/chat/send/ \'
echo '  -H "Content-Type: application/json" \'
echo '  -H "Authorization: Bearer YOUR_JWT_TOKEN" \'
echo '  -d '\''{"message": "Hello, can you help me learn Python?", "context": {"course_id": "test-123"}}'\'''

echo ""
echo "================================================"
echo "4. Check usage limits:"
echo ""
echo 'curl -X POST http://localhost:8000/api/v1/ai-assistant/user/check-limits/ \'
echo '  -H "Content-Type: application/json" \'
echo '  -H "Authorization: Bearer YOUR_JWT_TOKEN" \'
echo '  -d '\''{"agent_type": "chat", "estimated_tokens": 100}'\'''

echo ""
echo "================================================"
echo "5. Get AI stats:"
echo ""
echo 'curl -X GET http://localhost:8000/api/v1/ai-assistant/user/ai-stats/ \'
echo '  -H "Authorization: Bearer YOUR_JWT_TOKEN"'

echo ""
echo "================================================"
echo "NOTE: To get a valid JWT token:"
echo "1. Sign in through your frontend application"
echo "2. Use Supabase Auth API directly"
echo "3. Use the test_ai_assistant.py script"
echo "================================================"