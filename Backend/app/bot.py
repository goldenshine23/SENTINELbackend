import asyncio
import logging
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Optional
from metaapi_cloud_sdk import MetaApi

from config import META_API_TOKEN  # ✅ keep config import
from strategy.strategy import strategy  # ✅ keep import
from execution import trade_execution  # ⚠️ ensure trade_execution imported correctly

# FastAPI router
bot_router = APIRouter(prefix="/api/bot", tags=["Bot"])

# Dummy in-memory storage for bot status (for demo purposes)
bot_status_state = {"running": False}

# Broker details model
class BrokerDetails(BaseModel):
    broker_login: str
    broker_password: str
    server: str

# Simulate bot run (placeholder for MetaApi trading logic)
def run_bot_logic(broker_login: str, broker_password: str, server: str) -> str:
    logging.info(f"Running bot for: {broker_login}, Server: {server}")
    # Simulated trading logic
    return f"Bot started for account {broker_login} on server {server}"

# Endpoint: Simulated bot run
@bot_router.post("/run-bot")
async def run_bot(details: BrokerDetails):
    try:
        result = run_bot_logic(
            broker_login=details.broker_login,
            broker_password=details.broker_password,
            server=details.server
        )
        bot_status_state["running"] = True
        return {"message": result}
    except Exception as e:
        logging.error(f"Bot run failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run trading bot"
        )

# Endpoint: Bot status
@bot_router.get("/status")
async def bot_status():
    return {"running": bot_status_state["running"]}

# Endpoint: Example dummy route
@bot_router.get("/example")
def example():
    return {"message": "This is a bot route"}

# --- Actual MetaApi integrated logic ---

async def run_bot_for_user(broker_login, broker_password, server):
    # Initialize MetaApi inside this async function (not globally)
    metaapi = MetaApi(META_API_TOKEN)

    accounts = await metaapi.metatrader_account_api.get_accounts()
    for acc in accounts:
        if acc.login == broker_login and acc.server == server:
            return acc.__dict__

    account = await metaapi.metatrader_account_api.create_account({
        'name': f'{broker_login}',
        'type': 'cloud',
        'login': broker_login,
        'password': broker_password,
        'server': server,
        'platform': 'mt5'
    })

    await account.deploy()
    await account.wait_connected()

    connection = account.get_streaming_connection()
    await connection.connect()
    await connection.wait_synchronized()

    await strategy(connection)
    await trade_execution(connection)

    return account.__dict__

# Optional route using MetaAPI real logic (uncomment to use this instead of simulated one)
# @bot_router.post("/run-bot")
# async def run_bot(details: BrokerDetails):
#     try:
#         response = await run_bot_for_user(
#             details.broker_login,
#             details.broker_password,
#             details.server
#         )
#         return {"message": "Bot started successfully", "accountId": response['id']}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
