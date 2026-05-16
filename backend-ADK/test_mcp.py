import os
import json
from dotenv import load_dotenv

# Load env before importing app
load_dotenv(os.path.join(os.path.dirname(__file__), '.env.local'))

from app.services.mcp_client import mcp_client

print("Testing MCP client...")
results = mcp_client.search_docs("What are the compliance risks for Senior KYC Analyst?")
print("Result:")
print(json.dumps(results, indent=2))
