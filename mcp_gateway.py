import asyncio
import json
import sys
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
import httpx
import redis.asyncio as redis
from sqlalchemy.future import select
from prometheus_fastapi_instrumentator import Instrumentator
from database import SessionLocal, Role, AuditLog

app = FastAPI(title="Enterprise Policy-Aware MCP Gateway")

# --- OBSERVABILITY ---
Instrumentator().instrument(app).expose(app)

http_client = None
redis_client = None

@app.on_event("startup")
async def startup_event():
    global http_client, redis_client
    # MASSIVE SCALE FIX: Expand HTTP connection pool
    limits = httpx.Limits(max_connections=500, max_keepalive_connections=500)
    http_client = httpx.AsyncClient(timeout=30.0, limits=limits)
    
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    redis_client = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

@app.on_event("shutdown")
async def shutdown_event():
    await http_client.aclose()
    await redis_client.aclose()

async def check_rate_limit(agent_role: str) -> bool:
    key = f"rate_limit:{agent_role}"
    current = await redis_client.incr(key)
    if current == 1: 
        await redis_client.expire(key, 60)
    return current <= 2000

async def get_cached_permissions(agent_role: str, db) -> dict:
    cache_key = f"rbac:{agent_role}"
    cached = await redis_client.get(cache_key)
    if cached: 
        return json.loads(cached)
        
    result = await db.execute(select(Role).filter(Role.name == agent_role))
    role = result.scalars().first()
    if not role: 
        return None
        
    perms = {p.allowed_tool: p.restricted_argument for p in role.permissions}
    await redis_client.set(cache_key, json.dumps(perms), ex=300)
    return perms

async def semantic_llm_guardrail(text: str) -> str:
    restricted = ["Enterprise Data", "master key", "password", "confidential"]
    if any(c.lower() in text.lower() for c in restricted):
        return "[BLOCKED BY SEMANTIC AI GUARDRAIL]"
    return text

# --- THE PROXY WITH CONNECTION POOL PROTECTION ---
@app.post("/mcp/v1/tools/call")
async def proxy_tool_call_sse(request: Request):
    # 1. Identity Verification
    agent_role = request.headers.get("x-agent-role")
    if not agent_role:
        raise HTTPException(status_code=401, detail="Missing x-agent-role")

    # 2. Rate Limiting
    if not await check_rate_limit(agent_role):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    body = await request.json()
    tool_name = body.get("name")
    args = body.get("arguments", {})

    # 3. RBAC Inspection & Security Auditing (Isolated Sessions)
    async with SessionLocal() as db:
        perms = await get_cached_permissions(agent_role, db)
        
    if perms is None:
        raise HTTPException(status_code=403, detail="Role not found")

    if tool_name not in perms:
        async with SessionLocal() as session:
            async with session.begin():
                audit = AuditLog(agent_role=agent_role, requested_tool=tool_name, arguments_passed=str(args), action_taken="BLOCKED", reason="Unauthorized tool")
                session.add(audit)
        return {"error": f"SECURITY EXCEPTION: Unauthorized tool '{tool_name}'."}

    if perms[tool_name] != "None" and perms[tool_name] in args.values():
        async with SessionLocal() as session:
            async with session.begin():
                audit = AuditLog(agent_role=agent_role, requested_tool=tool_name, arguments_passed=str(args), action_taken="BLOCKED", reason="Restricted argument accessed")
                session.add(audit)
        return {"error": "SECURITY EXCEPTION: Restricted argument accessed."}

    async with SessionLocal() as session:
        async with session.begin():
            audit = AuditLog(agent_role=agent_role, requested_tool=tool_name, arguments_passed=str(args), action_taken="APPROVED", reason="Passed security")
            session.add(audit)

    # 4. SSE Stream
    async def event_stream():
        try:
            resp = await http_client.post("http://baseline_server:8001/mcp/v1/tools/call", json=body)
            result = resp.json()
            if "content" in result:
                for item in result["content"]:
                    if item.get("type") == "text":
                        item["text"] = await semantic_llm_guardrail(item["text"])
            yield f"data: {json.dumps(result)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield "event: close\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")