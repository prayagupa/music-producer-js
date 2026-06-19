#!/usr/bin/env bash
# Manual test script for MVP Feature 001: Music Producer App
# Generated: 2026-06-19
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8001}"
PASS=0; FAIL=0

run_test() {
  local name="$1"; local expected_status="$2"; local actual_status="$3"; local body="$4"
  if [[ "$actual_status" == "$expected_status" ]]; then
    echo "  ✅ PASS: $name"; ((PASS++)) || true
  else
    echo "  ❌ FAIL: $name (expected HTTP $expected_status, got $actual_status)"
    echo "     Response: $body"; ((FAIL++)) || true
  fi
}

assert_json_field() {
  local name="$1"; local json="$2"; local jq_expr="$3"; local expected="$4"
  local actual
  actual=$(echo "$json" | python3 -c "import sys,json; d=json.load(sys.stdin); print($jq_expr)" 2>/dev/null || echo "PARSE_ERROR")
  if [[ "$actual" == "$expected" ]]; then
    echo "  ✅ PASS: $name"; ((PASS++)) || true
  else
    echo "  ❌ FAIL: $name (expected '$expected', got '$actual')"; ((FAIL++)) || true
  fi
}

echo "=== Music Producer MVP Manual Tests ==="
echo "BASE_URL=$BASE_URL"
echo ""

# --- AC: Health endpoint returns API status ---
echo "--- Health ---"
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/v1/health")
BODY=$(echo "$RESPONSE" | sed '$d')
STATUS=$(echo "$RESPONSE" | tail -n 1)
run_test "Health returns 200" "200" "$STATUS" "$BODY"
assert_json_field "Health API check up" "$BODY" "d['checks']['api']" "up"

# --- AC: Create session ---
echo "--- Session Create ---"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/sessions" \
  -H "Content-Type: application/json" \
  -d '{"client_label":"manual-test"}')
BODY=$(echo "$RESPONSE" | sed '$d')
STATUS=$(echo "$RESPONSE" | tail -n 1)
run_test "Create session returns 200" "200" "$STATUS" "$BODY"
SESSION_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])")
if [[ -n "$SESSION_ID" ]]; then
  echo "  ✅ PASS: Session ID returned"; ((PASS++)) || true
else
  echo "  ❌ FAIL: No session_id in response"; ((FAIL++)) || true
fi

# --- AC: Generate music with mock LLM ---
echo "--- Generate ---"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/sessions/${SESSION_ID}/generate" \
  -H "Content-Type: application/json" \
  -d '{"message":"sad lo-fi beat","controls":{"tempo_bpm":80,"key":"Am","genre":"lo-fi","mood":"melancholic"}}')
BODY=$(echo "$RESPONSE" | sed '$d')
STATUS=$(echo "$RESPONSE" | tail -n 1)
run_test "Generate returns 200" "200" "$STATUS" "$BODY"
GENERATION_ID=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('generation_id',''))" 2>/dev/null || echo "")
assert_json_field "Generate preview_ready" "$BODY" "d.get('preview_ready')" "True"
assert_json_field "Generate provider mock" "$BODY" "d['metadata']['provider']" "mock"

# --- AC: MIDI download ---
echo "--- MIDI Download ---"
if [[ -n "$GENERATION_ID" ]]; then
  RESPONSE=$(curl -s -D /tmp/midi_headers.txt -w "\n%{http_code}" "$BASE_URL/api/v1/midi/${GENERATION_ID}")
  BODY=$(echo "$RESPONSE" | sed '$d')
  STATUS=$(echo "$RESPONSE" | tail -n 1)
  run_test "MIDI download returns 200" "200" "$STATUS" "(binary)"
  CONTENT_TYPE=$(grep -i '^content-type:' /tmp/midi_headers.txt | tr -d '\r' || true)
  if echo "$CONTENT_TYPE" | grep -qi "audio/midi"; then
    echo "  ✅ PASS: MIDI content-type audio/midi"; ((PASS++)) || true
  else
    echo "  ❌ FAIL: Expected audio/midi, got $CONTENT_TYPE"; ((FAIL++)) || true
  fi
  MIDI_SIZE=$(echo "$BODY" | wc -c | tr -d ' ')
  if [[ "$MIDI_SIZE" -gt 0 ]]; then
    echo "  ✅ PASS: MIDI bytes non-empty ($MIDI_SIZE bytes)"; ((PASS++)) || true
  else
    echo "  ❌ FAIL: MIDI response empty"; ((FAIL++)) || true
  fi
else
  echo "  ❌ FAIL: Skipped MIDI test — no generation_id"; ((FAIL++)) || true
fi

# --- AC: Get session (multi-turn context) ---
echo "--- Get Session ---"
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/api/v1/sessions/${SESSION_ID}")
BODY=$(echo "$RESPONSE" | sed '$d')
STATUS=$(echo "$RESPONSE" | tail -n 1)
run_test "Get session returns 200" "200" "$STATUS" "$BODY"
MSG_COUNT=$(echo "$BODY" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('messages',[])))" 2>/dev/null || echo "0")
if [[ "$MSG_COUNT" -ge 2 ]]; then
  echo "  ✅ PASS: Session has conversation messages ($MSG_COUNT)"; ((PASS++)) || true
else
  echo "  ❌ FAIL: Expected >=2 messages, got $MSG_COUNT"; ((FAIL++)) || true
fi

echo ""
echo "Results: $PASS passed, $FAIL failed out of $((PASS+FAIL)) tests"
[[ $FAIL -eq 0 ]] && exit 0 || exit 1
