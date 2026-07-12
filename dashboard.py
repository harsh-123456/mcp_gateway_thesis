import streamlit as st
import pandas as pd
from database import SessionLocal, AuditLog

# Configure the Streamlit page
st.set_page_config(page_title="MCP Gateway Security", page_icon="🛡️", layout="wide")
st.title("🛡️ MCP Gateway - Live Security Audit Dashboard")
st.markdown("Real-time monitoring of AI agent tool execution and RBAC policy enforcement.")

def fetch_audit_logs():
    db = SessionLocal()
    # Fetch all logs, newest first
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
    db.close()
    
    data = []
    for log in logs:
        data.append({
            "Timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "Agent Role": log.agent_role,
            "Target Tool": log.requested_tool,
            "Arguments": log.arguments_passed,
            "Action": log.action_taken,
            "Reason": log.reason
        })
    return pd.DataFrame(data)

# Load data
df = fetch_audit_logs()

if not df.empty:
    # 1. Top Level Metrics
    total_calls = len(df)
    approved_calls = len(df[df['Action'] == 'APPROVED'])
    blocked_calls = len(df[df['Action'] == 'BLOCKED'])
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Tool Invocations", total_calls)
    col2.metric("✅ Approved Requests", approved_calls)
    col3.metric("🚨 Blocked Threats", blocked_calls)
    
    st.divider()
    
    # 2. Dynamic Data Table with color coding
    st.subheader("Raw Audit Trail")
    
    def highlight_action(val):
        color = '#28a745' if val == 'APPROVED' else '#dc3545'
        return f'color: {color}; font-weight: bold'
    
    st.dataframe(
        df.style.map(highlight_action, subset=['Action']),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No audit logs found in the database. Run the client to generate traffic!")