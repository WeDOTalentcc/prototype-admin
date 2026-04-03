#!/bin/bash
# Step 1: Login and get MFA token
echo "=== Step 1: Login ==="
RESPONSE=$(curl -s -X POST 'https://api.wedotalent.cc/v1/sessions' \
  -H 'Content-Type: application/json' \
  -c /tmp/wedotalent-cookies.txt \
  -d '{"email":"paulo.moraes@wedotalent.cc","password":"Rodesia94"}')

echo "$RESPONSE"
MFA_TOKEN=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('mfa_token',''))")
echo "MFA_TOKEN=$MFA_TOKEN"
echo "$MFA_TOKEN" > /tmp/wedotalent-mfa-token.txt

echo ""
echo "=== WAITING FOR CODE ==="
echo "Write code to /tmp/2fa-code.txt"

# Wait for code
while true; do
  if [ -f /tmp/2fa-code.txt ]; then
    CODE=$(cat /tmp/2fa-code.txt)
    rm /tmp/2fa-code.txt
    if [ ${#CODE} -eq 6 ]; then
      break
    fi
  fi
  sleep 1
done

echo "=== Step 2: Verify MFA with code: $CODE ==="
VERIFY=$(curl -s -v -X POST 'https://api.wedotalent.cc/v1/sessions/verify_mfa' \
  -H 'Content-Type: application/json' \
  -b /tmp/wedotalent-cookies.txt \
  -c /tmp/wedotalent-cookies.txt \
  -d "{\"mfa_token\":\"$MFA_TOKEN\",\"code\":\"$CODE\"}" 2>&1)

echo "$VERIFY"
