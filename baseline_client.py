import asyncio
import httpx
import json

ACTIVE_ROLE = "internal_auditor" 

async def call_gateway_tool(tool_name: str, arguments: dict) -> dict:
    """Helper function to route an SSE streaming tool call through the gateway."""
    final_result = {}
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "http://127.0.0.1:8000/mcp/v1/tools/call",
            headers={"x-agent-role": ACTIVE_ROLE},
            json={"name": tool_name, "arguments": arguments}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    payload = line[6:]
                    if payload != "{}":
                        parsed_data = json.loads(payload)
                        if "content" in parsed_data or "isError" in parsed_data:
                            final_result = parsed_data
    return final_result

async def main():
    print(f"🧙‍♂️ Starting Multi-Step AI Agent Tool Chain Simulation...")
    print(f"Identity Context: {ACTIVE_ROLE}\n")
    
    # --- STEP 1: READ OPERATION ---
    print("Executing Step 1: Requesting system configuration data...")
    step_1_payload = {"filename": "config.yaml"}
    result_1 = await call_gateway_tool("read_sensitive_file", step_1_payload)
    print(f"↳ Step 1 Output: {result_1}\n")
    
    # Extract data to pass to the next step, simulating agent reasoning
    extracted_content = result_1.get("content", [{}])[0].get("text", "")
    
    # --- STEP 2: WRITE / SYNC OPERATION ---
    print("Executing Step 2: Forwarding processed data to sync system manifest...")
    step_2_payload = {"data": f"Processed backup from manifest content: {extracted_content[:30]}..."}
    result_2 = await call_gateway_tool("sync_system_manifest", step_2_payload)
    print(f"↳ Step 2 Output: {result_2}\n")
    
    print("🏆 Multi-step API dependency chain completed successfully through the gateway!")

if __name__ == "__main__":
    asyncio.run(main())