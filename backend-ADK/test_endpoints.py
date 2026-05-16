import os
from dotenv import load_dotenv

# Load env before importing app
load_dotenv(os.path.join(os.path.dirname(__file__), '.env.local'))

from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

def run_tests():
    print("Testing Vidda API Endpoints...")
    print("-" * 50)

    # 1. Test Governance Stats (GET)
    print("1. Testing GET /governance/stats ...")
    response = client.get("/governance/stats")
    if response.status_code == 200:
        print(f"✅ Success! Data: {response.json()}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")

    # 2. Test Regulations Search (POST)
    print("\n2. Testing POST /regulations/search ...")
    response = client.post("/regulations/search", json={"query": "onboarding", "risk_types": ["onboarding_risk"]})
    if response.status_code == 200:
        matches = response.json().get("matches", [])
        print(f"✅ Success! Found {len(matches)} regulations.")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")

    # 3. Test Workflow Run (POST)
    # This might take 30-40 seconds because of LLMs
    print("\n3. Testing POST /workflow/run (This triggers the multi-agent ADK workflow and might take ~30s)...")
    workflow_payload = {
        "uploaded_text": "Role: KYC Analyst. Responsible for customer due diligence and identity verification."
    }
    response = client.post("/workflow/run", json=workflow_payload)
    plan_id = None
    if response.status_code == 200:
        data = response.json()
        plan_id = data.get("training_plan_id")
        print(f"✅ Success! Generated Plan ID: {plan_id}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")

    # 4. Test Workflow Revise (POST) - Depends on step 3
    if plan_id:
        print(f"\n4. Testing POST /workflow/revise/{plan_id} (Human in the loop feedback)...")
        revise_payload = {"feedback": "Add more focus on transaction monitoring"}
        response = client.post(f"/workflow/revise/{plan_id}", json=revise_payload)
        if response.status_code == 200:
            print(f"✅ Success! Agent processed feedback: {response.json()}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            
    print("-" * 50)
    print("Test Suite Completed.")

if __name__ == "__main__":
    run_tests()
