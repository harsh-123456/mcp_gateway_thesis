import asyncio
import httpx
import time
import pandas as pd

# Target Endpoints (Mapped through Docker to your local machine)
GATEWAY_URL = "http://127.0.0.1:8000/mcp/v1/tools/call"
BASELINE_URL = "http://127.0.0.1:8001/mcp/v1/tools/call"

# Test Scenarios
NUM_ITERATIONS = 20

payload_safe = {"name": "read_sensitive_file", "arguments": {"filename": "config.yaml"}}
payload_unsafe = {"name": "read_sensitive_file", "arguments": {"filename": "master_key.pem"}}
headers_auditor = {"x-agent-role": "internal_auditor"}
headers_public = {"x-agent-role": "public_agent"}

results = []

async def measure_request(target_url, headers, payload, scenario_name, expected_action):
    start_time = time.perf_counter()
    status = "FAILED"
    
    async with httpx.AsyncClient() as client:
        try:
            # We use a standard POST here for the benchmark to measure raw HTTP overhead
            response = await client.post(target_url, headers=headers, json=payload, timeout=5.0)
            data = response.text  # Fixed: Reading raw text stream instead of parsing as JSON
            
            # Determine success or block based on the response payload
            if "SECURITY EXCEPTION" in data:
                status = "BLOCKED"
            elif "ACTUAL CORPORATE FILE" in data or "data:" in data:
                status = "APPROVED"
                
        except Exception as e:
            status = f"ERROR: {str(e)}"
            
    end_time = time.perf_counter()
    latency_ms = (end_time - start_time) * 1000
    
    # Check if the system behaved as we expected
    policy_enforced = (status == expected_action)

    results.append({
        "Scenario": scenario_name,
        "Latency (ms)": round(latency_ms, 2),
        "Action Taken": status,
        "Policy Enforced Correctly": policy_enforced
    })

async def run_benchmark():
    print("🚀 Initiating Thesis Evaluation Benchmark Suite...")
    print(f"Running {NUM_ITERATIONS} iterations per scenario. Please wait...\n")
    
    tasks = []
    
    # SCENARIO 1: Direct Baseline Access (The Control Group - No Security)
    # Measures raw speed without the gateway.
    for _ in range(NUM_ITERATIONS):
        tasks.append(measure_request(BASELINE_URL, headers_auditor, payload_safe, "1. Direct Baseline (Control)", "APPROVED"))
        
    # SCENARIO 2: Gateway Safe Access (Overhead Measurement)
    # Measures how much latency the RBAC engine and SQLite logging add to a valid request.
    for _ in range(NUM_ITERATIONS):
        tasks.append(measure_request(GATEWAY_URL, headers_auditor, payload_safe, "2. Gateway Allowed Request", "APPROVED"))
        
    # SCENARIO 3: Gateway Blocked Access (Security Effectiveness)
    # Measures the gateway successfully intercepting an unsafe file request.
    for _ in range(NUM_ITERATIONS):
        tasks.append(measure_request(GATEWAY_URL, headers_auditor, payload_unsafe, "3. Gateway Blocked File", "BLOCKED"))

    # SCENARIO 4: Gateway Unauthorized Role (Identity Verification)
    for _ in range(NUM_ITERATIONS):
         tasks.append(measure_request(GATEWAY_URL, headers_public, payload_safe, "4. Gateway Blocked Role", "BLOCKED"))

    await asyncio.gather(*tasks)
    
    # Process and Export Results
    df = pd.DataFrame(results)
    
    # Calculate Averages
    summary = df.groupby("Scenario").agg({
        "Latency (ms)": "mean",
        "Policy Enforced Correctly": "mean" # 1.0 means 100% success rate
    }).rename(columns={"Latency (ms)": "Avg Latency (ms)", "Policy Enforced Correctly": "Security Success Rate"})
    
    summary["Security Success Rate"] = (summary["Security Success Rate"] * 100).astype(str) + "%"
    
    print("📊 --- BENCHMARK SUMMARY ---")
    print(summary.to_string())
    print("\n✅ Benchmark complete. Exporting full dataset to 'thesis_benchmark_results.csv'...")
    
    df.to_csv("thesis_benchmark_results.csv", index=False)

if __name__ == "__main__":
    asyncio.run(run_benchmark())