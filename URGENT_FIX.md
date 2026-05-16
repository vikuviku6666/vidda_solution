# URGENT FIX - Backend Hanging Issue

## Problem
- Backend is hanging/crashing on all requests
- Frontend shows empty data (Workflow Data: null)
- API calls timeout after 30+ seconds

## Root Cause
Backend was NOT loading `.env` file on startup, causing API calls to fail silently or hang.

## ✅ FIXED
Added `load_dotenv()` to `/backend-ADK/app/main.py`

## 🚀 HOW TO RESTART & TEST

### Step 1: Stop Everything
```bash
# Stop backend (if running)
pkill -f "uvicorn app.main"

# Stop frontend (if running)
# Press Ctrl+C in frontend terminal
```

### Step 2: Start Backend (Watch for Errors!)
```bash
cd /Users/viku/Dev_Projects/vidda/backend-ADK
python -m uvicorn app.main:app --reload --port 8000
```

**Watch startup logs for:**
- ✅ "Application startup complete"
- ✅ "Uvicorn running on http://127.0.0.1:8000"
- ❌ ANY error messages (report them!)

### Step 3: Test Backend API
```bash
# In NEW terminal, test the API:
curl -X POST http://127.0.0.1:8000/workflow/run \
  -H "Content-Type: application/json" \
  -d '{"uploaded_text": "Compliance Officer for AML"}' \
  --max-time 60

# Should return JSON response in 25-35 seconds
# If it times out or hangs, CHECK BACKEND LOGS!
```

### Step 4: Start Frontend
```bash
cd /Users/viku/Dev_Projects/vidda/frontend/my-app
npm run dev
```

### Step 5: Test Full Flow
1. Open http://localhost:3000
2. Paste role: "KYC Analyst responsible for customer due diligence"
3. Click "Process Role Description"
4. Should complete in 25-35 seconds

## 🔍 IF STILL HANGING

### Check 1: Backend Logs
Look for these specific errors:

```bash
# Error 1: API Key Missing
KeyError: 'OPENROUTER_API_KEY'
→ Solution: Restart backend (it should load .env now)

# Error 2: API Key Invalid
401 Unauthorized from openrouter.ai
→ Solution: Check API key is valid

# Error 3: RAG Endpoint Down
Connection timeout to rag.bluetext.dev
→ Solution: Check RAG service status

# Error 4: Import Error
ModuleNotFoundError: No module named 'dotenv'
→ Solution: pip install python-dotenv
```

### Check 2: Test API Keys Directly

**Test OpenRouter:**
```bash
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer sk-or-v1-REDACTED"

# Should return list of models (200 OK)
# If 401: API key invalid
# If timeout: Network issue
```

**Test RAG Endpoint:**
```bash
curl -X POST https://rag.bluetext.dev/mcp/ \
  -H "Authorization: Bearer rag_REDACTED" \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}' \
  --max-time 10

# Should return search results (200 OK)
# If 401: API key invalid
# If timeout: RAG service down
```

### Check 3: Environment Variables Loading

```bash
cd /Users/viku/Dev_Projects/vidda/backend-ADK
python3 << 'PYTHON'
from dotenv import load_dotenv
import os

load_dotenv()

print("=" * 60)
print("ENVIRONMENT VARIABLES CHECK")
print("=" * 60)

keys = {
    'OPENROUTER_API_KEY': os.getenv('OPENROUTER_API_KEY'),
    'LLM_MODEL': os.getenv('LLM_MODEL'),
    'RAG_API_KEY': os.getenv('RAG_API_KEY'),
    'RAG_ENDPOINT': os.getenv('RAG_ENDPOINT'),
}

for key, value in keys.items():
    if value:
        display = value[:20] + '...' if len(value) > 20 else value
        print(f"✅ {key}: {display}")
    else:
        print(f"❌ {key}: MISSING!")

print("=" * 60)
PYTHON
```

**Expected output:**
```
✅ OPENROUTER_API_KEY: sk-or-v1-REDACTED...
✅ LLM_MODEL: google/gemini-2.5-flash
✅ RAG_API_KEY: rag_REDACTED...
✅ RAG_ENDPOINT: https://rag.bluetext...
```

## 📝 WHAT WAS CHANGED

### File: `/backend-ADK/app/main.py`

**Before:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.audit import router as audit_router
```

**After:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.routes.audit import router as audit_router
```

## 🆘 EMERGENCY DEBUGGING

If backend still hangs, add debug logging:

**Edit `backend-ADK/app/services/workflow.py`:**

Add at the very top (line 1):
```python
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
```

This will show EVERY operation and where it's hanging.

## ✅ SUCCESS CRITERIA

After fix, you should see:

**Backend startup:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**API call:**
```
INFO: Starting Role Extraction...
INFO: ✅ Role extracted: Compliance Officer (3.2s)
INFO: Starting PARALLEL RAG extraction...
INFO: ⚡ PARALLEL extraction completed in 11.8s
INFO: ✅ Training plan generated (10.2s)
INFO: 🎯 TOTAL WORKFLOW TIME: 25.8s
```

**Frontend:**
```
Workflow Data: { role_data: {...}, training_plan: {...} }
Modules: [{ module_name: "...", quarter: "Q1", ... }, ...]
```

## 📞 NEXT STEPS

1. **Restart backend** with the fix
2. **Watch logs carefully**
3. **Test API with curl**
4. **Test frontend**
5. **Report any new errors** you see

The `.env` file is now properly configured and `load_dotenv()` has been added to `main.py`. The backend SHOULD work now!
