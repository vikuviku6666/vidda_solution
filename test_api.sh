#!/bin/bash
echo "Testing Backend API..."
echo ""

curl -s -X POST http://127.0.0.1:8000/workflow/run \
  -H "Content-Type: application/json" \
  -d '{"uploaded_text": "KYC Analyst responsible for customer due diligence, transaction monitoring, and risk assessment for high-risk clients in the financial services sector"}' \
  --max-time 60 | python3 -m json.tool | head -100

echo ""
echo "Done!"
