import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy import Column, Integer, String, ForeignKey

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = "5432" if DB_HOST == "db" else "5433"
# UPGRADED: Using asyncpg for true non-blocking I/O
SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://admin:adminpassword@{DB_HOST}:{DB_PORT}/gateway_db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=20,
    max_overflow=5
)

SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    permissions = relationship("Permission", back_populates="role", lazy="selectin")

class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    allowed_tool = Column(String)
    restricted_argument = Column(String, default="None")
    role = relationship("Role", back_populates="permissions")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    agent_role = Column(String)
    requested_tool = Column(String)
    arguments_passed = Column(String)
    action_taken = Column(String)
    reason = Column(String)

async def init_db():
    """Asynchronously create tables on startup"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)