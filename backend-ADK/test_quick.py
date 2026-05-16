#!/usr/bin/env python3
"""Quick test to verify API keys and basic functionality"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

print("=" * 70)
print("QUICK API TEST")
print("=" * 70)

# Test 1: Environment Variables
print("\n1. Testing Environment Variables...")
required_vars = {
    'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY'),
    'LLM_MODEL': os.getenv('LLM_MODEL'),
    'RAG_API_KEY': os.getenv('RAG_API_KEY'),
    'RAG_ENDPOINT': os.getenv('RAG_ENDPOINT'),
}

all_set = True
for key, value in required_vars.items():
    if value:
        display = value[:25] + '...' if len(value) > 25 else value
        print(f"   ✅ {key}: {display}")
    else:
        print(f"   ❌ {key}: MISSING!")
        all_set = False

if not all_set:
    print("\n❌ Some environment variables are missing!")
    print("   Check your .env file")
    sys.exit(1)

# Test 2: OpenRouter API
print("\n2. Testing OpenRouter API...")
try:
    from app.services.llm_client import create_llm_client, llm_model_name
    client = create_llm_client()
    model = llm_model_name()
    print(f"   ✅ LLM Client created successfully")
    print(f"   ✅ Model: {model}")
    
    # Quick test call
    print("   📡 Making test LLM call...")
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Say 'test successful' in 2 words"}],
        max_tokens=10
    )
    result = response.choices[0].message.content
    print(f"   ✅ LLM Response: {result}")
except Exception as e:
    print(f"   ❌ LLM Test Failed: {e}")
    sys.exit(1)

# Test 3: RAG/MCP API
print("\n3. Testing RAG/MCP API...")
try:
    from app.services.mcp_client import mcp_search_tool_func
    print("   📡 Making test RAG query...")
    results = mcp_search_tool_func("AMLR Article")
    print(f"   ✅ RAG Search returned {len(results)} results")
    if results:
        print(f"   ✅ Sample result: {str(results[0])[:100]}...")
except Exception as e:
    print(f"   ❌ RAG Test Failed: {e}")
    sys.exit(1)

# Test 4: Quick Workflow Test
print("\n4. Testing Workflow (Quick)...")
try:
    from app.services.role_intelligence import extract_role_intelligence
    print("   📡 Extracting role from sample text...")
    role_data = extract_role_intelligence("Compliance Officer for AML")
    print(f"   ✅ Role extracted: {role_data.role}")
    print(f"   ✅ Responsibilities: {len(role_data.responsibilities)} items")
except Exception as e:
    print(f"   ❌ Workflow Test Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED!")
print("=" * 70)
print("\nYou can now start the server:")
print("  python -m uvicorn app.main:app --reload --port 8000")
print("=" * 70)
