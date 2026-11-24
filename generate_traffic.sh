#!/usr/bin/env bash
# Sends a mix of normal, failing and suspicious requests so Splunk has data to look at.
# Usage: ./generate_traffic.sh [base_url] [requests]
URL="${1:-http://127.0.0.1}"
N="${2:-200}"
AGENTS=("Mozilla/5.0 (Windows NT 10.0)" "Mozilla/5.0 (Macintosh)" "curl/8.5" "python-requests/2.32" "sqlmap/1.8")

for ((i = 1; i <= N; i++)); do
  UA="${AGENTS[RANDOM % ${#AGENTS[@]}]}"
  case $((RANDOM % 12)) in
    0|1|2) curl -s -o /dev/null -A "$UA" "$URL/api/products" ;;
    3|4)   curl -s -o /dev/null -A "$UA" "$URL/api/products/$((RANDOM % 6 + 1))" ;;
    5)     curl -s -o /dev/null -A "$UA" -H 'Content-Type: application/json' \
             -d '{"username":"alice","password":"wonderland"}' "$URL/api/login" ;;
    6)     curl -s -o /dev/null -A "$UA" -H 'Content-Type: application/json' \
             -d "{\"username\":\"admin\",\"password\":\"guess$RANDOM\"}" "$URL/api/login" ;;
    7|8)   curl -s -o /dev/null -A "$UA" -H 'Content-Type: application/json' \
             -d "{\"product_id\":$((RANDOM % 4 + 1)),\"quantity\":$((RANDOM % 3 + 1))}" "$URL/api/orders" ;;
    9)     curl -s -o /dev/null -A "$UA" "$URL/api/error" ;;
    10)    curl -s -o /dev/null -A "$UA" "$URL/api/slow" ;;
    11)    curl -s -o /dev/null -A "$UA" "$URL/wp-login.php?id=1%27%20OR%201=1--" ;;
  esac
  sleep 0.$((RANDOM % 5))
done
echo "Sent $N requests to $URL"
