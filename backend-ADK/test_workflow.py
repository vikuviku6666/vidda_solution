import os
import json
from dotenv import load_dotenv

# Load env before importing app
load_dotenv(os.path.join(os.path.dirname(__file__), '.env.local'))

from app.services.workflow import run_training_workflow

def test():
    print("Testing the Multi-Agent Workflow...")
    text = "Role: Senior KYC Analyst. Responsibilities include customer due diligence, reviewing alerts, and reporting suspicious activities."
    print(f"Input Text: {text}\n")
    
    try:
        response = run_training_workflow(text)
        print("Success! Response:")
        print(f"Role Data: {response.role_data.model_dump()}")
        print(f"Risks Found: {response.risks}")
        print(f"Regulations Found: {len(response.regulations)}")
        print(f"Recommendations Generated: {len(response.recommendations)}")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
