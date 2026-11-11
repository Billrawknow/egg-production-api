#!/usr/bin/env bash
# Test the Egg Production API with curl. Start the server first: python app.py
# If you set EGG_API_KEY in .env, run:  API_KEY=yourkey bash test_requests.sh
URL="http://127.0.0.1:5000/api/eggs"
KEY_HEADER=()
[ -n "$API_KEY" ] && KEY_HEADER=(-H "X-API-Key: $API_KEY")

post() {
  echo "POST $1"
  curl -s -X POST "$URL" "${KEY_HEADER[@]}" -H "Content-Type: application/json" -d "$1"
  echo; echo
}

echo "=== 4 valid records across two sheds ==="
post '{"shed": "A", "date": "2026-11-09", "count": 412}'
post '{"shed": "B", "date": "2026-11-09", "count": 388}'
post '{"shed": "A", "date": "2026-11-10", "count": 405}'
post '{"shed": "B", "date": "2026-11-10", "count": 396}'

echo "=== Requests that should be rejected ==="
post '{"shed": "A", "date": "2026-11-10", "count": 400}'      # duplicate -> 409
post '{"shed": "D", "date": "2026-11-10", "count": 100}'      # unknown shed -> 400
post '{"shed": "B", "date": "10/11/2026", "count": 100}'      # bad date -> 400
post '{"shed": "B", "date": "2026-11-11", "count": "many"}'   # bad count -> 400
post '{"shed": "B", "count": 100}'                            # missing date -> 400

echo "=== GET all records with running totals ==="
curl -s "$URL" "${KEY_HEADER[@]}"
echo; echo
echo "=== GET shed A only ==="
curl -s "$URL?shed=A" "${KEY_HEADER[@]}"
echo
