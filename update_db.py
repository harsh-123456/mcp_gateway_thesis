from database import SessionLocal, Role, Permission

def grant_permission():
    db = SessionLocal()
    
    # Find the internal_auditor role
    auditor = db.query(Role).filter(Role.name == "internal_auditor").first()
    
    if auditor:
        # Grant the new tool permission
        new_perm = Permission(
            role_id=auditor.id, 
            allowed_tool="sync_system_manifest", 
            restricted_argument="None"
        )
        db.add(new_perm)
        db.commit()
        print("✅ SUCCESS: Granted 'sync_system_manifest' permission to internal_auditor.")
    else:
        print("❌ ERROR: Role not found.")
        
    db.close()

if __name__ == "__main__":
    grant_permission()