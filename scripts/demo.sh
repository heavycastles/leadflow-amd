#!/usr/bin/env bash
# Feeds sample multilingual leads into a running app (default http://localhost:8080) and prints the ranking.
set -euo pipefail
URL="${1:-http://localhost:8080}"
post() { curl -s -X POST "$URL/leads" -H 'Content-Type: application/json' -d "$1" >/dev/null; }
post '{"name":"Ivan","source":"whatsapp","phone":"+998901112233","message":"Хочу заказать 2 шт кроссовки 42 размера, срочно, бюджет 900000 сум"}'
post '{"name":"Dilnoza","source":"telegram","phone":"+998935550011","message":"Salom! 3 dona kurtka kerak, bugun olaman. Narxi qancha?"}'
post '{"name":"Sarah","source":"web","email":"sarah@example.com","message":"What is the price for 50 units hoodies with logo?"}'
post '{"name":"Aziz","source":"telegram","phone":"+998935556677","message":"Kurtka brak keldi, pulni qaytaring"}'
post '{"name":"Bot","source":"web","email":"win@spam.io","message":"Crypto bonus casino click here"}'
curl -s "$URL/leads" | python3 -c '
import json,sys
for l in json.load(sys.stdin)["leads"]:
    g=l["agent"]; a=g["analysis"]; m=g["llm"]
    print(g["hybrid_score"], l["name"], a["intent"], a["next_action"], m["backend"], str(m["latency_ms"])+"ms", a["reply"][:60], sep=" | ")'
echo; curl -s "$URL/orders"; echo; curl -s "$URL/metrics"; echo
