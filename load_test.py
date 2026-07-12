import asyncio
import httpx
import time

GATEWAY_URL = "http://127.0.0.1:8000/mcp/v1/tools/call"
TOTAL_REQUESTS = 1000
CONCURRENT_CONNECTIONS = 100

payload = {"name": "read_sensitive_file", "arguments": {"filename": "config.yaml"}}
headers = {"x-agent-role": "internal_auditor"}

async def make_request(client):
    try:
        # Timeout increased to 30.0 to prevent premature client disconnects under heavy load
        response = await client.post(GATEWAY_URL, headers=headers, json=payload, timeout=30.0)
        return response.status_code == 200
    except Exception:
        return False

async def run_load_test():
    print(f"🔥 INITIATING EXTREME LOAD TEST: {TOTAL_REQUESTS} Requests...")
    
    # We use limits to simulate massive concurrent traffic
    limits = httpx.Limits(max_connections=CONCURRENT_CONNECTIONS, max_keepalive_connections=CONCURRENT_CONNECTIONS)
    
    start_time = time.perf_counter()
    
    async with httpx.AsyncClient(limits=limits) as client:
        tasks = [make_request(client) for _ in range(TOTAL_REQUESTS)]
        results = await asyncio.gather(*tasks)
        
    end_time = time.perf_counter()
    
    successful = sum(results)
    failed = TOTAL_REQUESTS - successful
    total_time = end_time - start_time
    rps = TOTAL_REQUESTS / total_time
    
    print("\n📊 --- LOAD TEST RESULTS ---")
    print(f"Total Time: {total_time:.2f} seconds")
    print(f"Successful Requests: {successful}")
    print(f"Failed Requests: {failed}")
    print(f"Throughput: {rps:.2f} Requests Per Second (RPS)")
    
    if failed == 0:
        print("\n✅ ENTERPRISE GRADE: Gateway handled maximum load with 0% failure rate!")
    else:
        print(f"\n⚠️ SYSTEM STRESSED: {failed} requests dropped under load.")

if __name__ == "__main__":
    asyncio.run(run_load_test())