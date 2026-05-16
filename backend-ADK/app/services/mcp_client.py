import os
import json
import threading
import httpx
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env.local'))

RAG_ENDPOINT = os.getenv("RAG_ENDPOINT", "https://rag.bluetext.dev/mcp/")
RAG_API_KEY = os.getenv("RAG_API_KEY")

class MCPRAGClient:
    def __init__(self):
        self.endpoint = RAG_ENDPOINT
        self.api_key = RAG_API_KEY
        self.session_id = None
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        # Thread-local storage so each thread gets its own httpx.Client,
        # avoiding connection-pool lock contention under concurrent calls.
        self._local = threading.local()

        if self.api_key:
            self._initialize()

    def _get_client(self) -> httpx.Client:
        """Return a per-thread httpx.Client (created on first use in each thread)."""
        if not hasattr(self._local, "client"):
            self._local.client = httpx.Client(timeout=30.0)
        return self._local.client

    def _post_jsonrpc(self, payload: dict) -> httpx.Response:
        headers = self.headers.copy()
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        client = self._get_client()
        response = client.post(self.endpoint, json=payload, headers=headers)
        response.raise_for_status()

        if not self.session_id and "Mcp-Session-Id" in response.headers:
            self.session_id = response.headers["Mcp-Session-Id"]

        return response


    def _initialize(self):
        init_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "vidda-backend", "version": "1.0.0"}
            }
        }
        self._post_jsonrpc(init_payload)
        
        notif_payload = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        self._post_jsonrpc(notif_payload)

    def search_docs(self, query: str, project_id: str = None) -> list[dict]:
        """
        Queries the MCP RAG server for documents matching the query.
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "search_docs",
                "arguments": {
                    "query": query
                }
            }
        }
        if project_id:
            payload["params"]["arguments"]["project_id"] = project_id

        response = self._post_jsonrpc(payload)
        content_type = response.headers.get("Content-Type", "")
        
        if "text/event-stream" in content_type:
            lines = response.text.split("\n")
            result_data = None
            for line in lines:
                if line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        data = json.loads(data_str)
                        if "result" in data:
                            result_data = data["result"]
                    except:
                        pass
            
            return self._parse_mcp_result(result_data)
        else:
            data = response.json()
            return self._parse_mcp_result(data.get("result"))
            
    def _parse_mcp_result(self, result_data: dict) -> list[dict]:
        if not result_data:
            return []
            
        if "content" in result_data:
            for item in result_data["content"]:
                if item.get("type") == "text":
                    try:
                        # Sometimes MCP returns the array as a JSON string inside the text
                        parsed = json.loads(item["text"])
                        if isinstance(parsed, dict):
                            return [parsed]
                        elif isinstance(parsed, list):
                            return parsed
                        else:
                            return [{"text": str(parsed)}]
                    except:
                        # Otherwise just return the text
                        return [{"text": item["text"]}]
        return []

# Singleton instance
mcp_client = MCPRAGClient()

def mcp_search_tool_func(query: str) -> list[dict]:
    """
    Search the company's central MCP RAG system. 
    Use this to find risk mappings for roles, or AMLR regulations for specific risks.
    """
    return mcp_client.search_docs(query)

from google.adk.tools import FunctionTool
mcp_search_tool = FunctionTool(func=mcp_search_tool_func)
