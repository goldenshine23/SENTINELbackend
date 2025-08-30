# backend/main.py

import sys
import os
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# === Fix import paths for local modules ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

# === Local imports ===
from app.database import engine, SessionLocal
from app.models import Base, User  # Ensure models are registered before table creation
from app.routes import router as api_router  # Includes auth and bot routes
from execution import run_trading_for_all_users  # Your trading logic
from app.routes import router as api_router

# === Create DB tables once ===
Base.metadata.create_all(bind=engine)

# === Initialize FastAPI ===
app = FastAPI(title="SentinelAI Bot")

# === CORS (open for now) ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Register all routes ===
app.include_router(api_router, prefix="/api")

# === Root endpoint ===
@app.get("/")
def read_root():
    return {"message": "🚀 Welcome to SentinelAI Bot API"}

# === Helper: Get all active users ===
def get_all_active_users():
    db = SessionLocal()
    try:
        return db.query(User).filter(User.bot_active == True).all()
    finally:
        db.close()

# === Trading logic background task ===
async def main():
    print("🟢 Trading Engine Starting...")
    users = get_all_active_users()
    if users:
        await run_trading_for_all_users(users)
    else:
        print("⚠️ No active users found. Trading Engine paused.")

# === Entry point for async trading when run directly ===
if __name__ == "__main__":
    asyncio.run(main())
# backend/main.py

from fastapi import FastAPI
from app.routes import router as api_router

app = FastAPI(title="SentinelAI Bot")

app.include_router(api_router)
