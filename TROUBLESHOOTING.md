# Troubleshooting Guide

## Issue: Application Stuck at "Generating quarterly training plan..."

### Symptoms
- Frontend shows loading spinner
- Progress stops at "Generating quarterly training plan..."
- Backend appears to hang (high CPU usage)
- No response after 30+ seconds

### Root Causes

#### 1. Missing or Incorrect API Keys
**Solution:**
```bash
# Check if .env file exists
ls -la backend-ADK/.env

# If missing, copy from .env.local or create new
cp backend-ADK/.env.local backend-ADK/.env

# Verify keys are present (will show masked values)
grep -E "OPENROUTER|RAG" backend-ADK/.env | sed 's/=.*/=***CONFIGURED***/'
```

**Required keys:**
- `OPENROUTER_API_KEY` - For LLM (Google Gemini via OpenRouter)
- `RAG_API_KEY` - For RAG document retrieval
- `RAG_ENDPOINT` - RAG endpoint URL

#### 2. Backend Not Loading .env File
**Solution:**
```bash
# Stop backend
pkill -f "uvicorn app.main:app"

# Restart backend (it will reload .env)
cd backend-ADK
python -m uvicorn app.main:app --reload --port 8000
```

#### 3. API Key Invalid or Expired
**Check:**
```bash
# Test OpenRouter API
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer YOUR_OPENROUTER_KEY"

# Test RAG endpoint
curl -X POST https://rag.bluetext.dev/mcp/ \
  -H "Authorization: Bearer YOUR_RAG_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

#### 4. Network Issues
**Check:**
```bash
# Test connectivity to OpenRouter
curl -I https://openrouter.ai

# Test connectivity to RAG endpoint
curl -I https://rag.bluetext.dev
```

#### 5. Backend Logs Show Errors
**Check backend terminal for:**
- `401 Unauthorized` - Invalid API key
- `429 Too Many Requests` - Rate limit exceeded
- `Connection timeout` - Network issues
- `KeyError` - Missing environment variable

### Quick Fix Steps

1. **Stop the backend:**
   ```bash
   # Press Ctrl+C in backend terminal
   # OR
   pkill -f "uvicorn app.main:app"
   ```

2. **Verify .env file:**
   ```bash
   cd backend-ADK
   cat .env
   ```
   
   Should contain:
   ```
   OPENROUTER_API_KEY=sk-or-v1-REDACTED...
   LLM_MODEL=google/gemini-2.5-flash
   RAG_API_KEY=rag_REDACTED...
   RAG_ENDPOINT=https://rag.bluetext.dev/mcp/
   DATABASE_URL=sqlite:///vidda.db
   ```

3. **Restart backend:**
   ```bash
   cd backend-ADK
   python -m uvicorn app.main:app --reload --port 8000
   ```

4. **Refresh frontend:**
   ```bash
   # In browser, refresh page or restart frontend
   cd frontend/my-app
   npm run dev
   ```

5. **Try again:**
   - Submit role description
   - Watch backend logs for errors
   - Should complete in 25-35 seconds

### Debug Mode

Add verbose logging to see exactly where it hangs:

**backend-ADK/app/services/workflow.py:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Then check logs for:
- LLM requests
- RAG queries
- Response times
- Error messages

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `KeyError: 'OPENROUTER_API_KEY'` | Missing env var | Add to .env |
| `401 Unauthorized` | Invalid API key | Check key value |
| `Connection timeout` | Network issue | Check connectivity |
| `429 Too Many Requests` | Rate limit | Wait and retry |
| `Module not found` | Missing dependency | `pip install -r requirements.txt` |

### Still Stuck?

1. **Check all backend logs carefully**
2. **Test API keys independently**
3. **Verify Python dependencies installed**
4. **Check if ports 8000 and 3000 are available**
5. **Try with a shorter role description first**

### Contact

- Review: [ARCHITECTURE.md](ARCHITECTURE.md)
- Check: [READY_TO_TEST.md](READY_TO_TEST.md)
- Open issue: https://github.com/vikuviku6666/vidda_solution/issues
