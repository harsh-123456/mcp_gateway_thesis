import asyncio
from sqlalchemy.future import select
from database import SessionLocal, Role, Permission, init_db

async def seed():
    await init_db()
    
    async with SessionLocal() as db:
        result = await db.execute(select(Role).filter(Role.name == "internal_auditor"))
        existing_role = result.scalars().first()
        
        if existing_role:
            print("Database already seeded!")
            return

        role = Role(name="internal_auditor")
        db.add(role)
        await db.commit()
        await db.refresh(role)

        perm1 = Permission(role_id=role.id, allowed_tool="read_sensitive_file", restricted_argument="master_key.pem")
        perm2 = Permission(role_id=role.id, allowed_tool="sync_system_manifest", restricted_argument="None")
        
        db.add_all([perm1, perm2])
        await db.commit()
        
        print("✅ Async PostgreSQL Database Seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed())