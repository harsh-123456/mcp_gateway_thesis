import sys
from fastapi import FastAPI, Request

app = FastAPI(title="Real Baseline MCP Server")

print("Baseline Server initialized. Listening for approved requests on port 8001...", file=sys.stderr)

@app.post("/mcp/v1/tools/call")
async def execute_tool(request: Request):
    """
    This server ONLY executes tools. It has no security.
    It trusts the Gateway to do all the filtering.
    """
    body = await request.json()
    tool_name = body.get("name")
    arguments = body.get("arguments", {})
    
    print(f"[BASELINE LOG] Received request from Gateway to execute: '{tool_name}'", file=sys.stderr)
    
    # --- TOOL 1: READ SENSITIVE FILE ---
    if tool_name == "read_sensitive_file":
        filename = arguments.get("filename")
        data = f"ACTUAL CORPORATE FILE CONTENTS of {filename}: [Highly Confidential Enterprise Data]"
        print(f"[BASELINE LOG] Successfully read {filename}. Returning payload to Gateway.", file=sys.stderr)
        return {"content": [{"type": "text", "text": data}]}
        
    # --- TOOL 2: SYNC SYSTEM MANIFEST (NEW MULTI-STEP TOOL) ---
    elif tool_name == "sync_system_manifest":
        manifest_data = arguments.get("data")
        print(f"[BASELINE LOG] Received command to sync manifest data: '{manifest_data}'", file=sys.stderr)
        return {"content": [{"type": "text", "text": "SYSTEM MANIFEST SYNCED SUCCESSFULLY: Write operation verified."}]}
        
    return {"error": "Tool not found on baseline server"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)