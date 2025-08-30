import asyncio
from metaapi_cloud_sdk import MetaApi
import os
from dotenv import load_dotenv

load_dotenv()
META_API_TOKEN = os.getenv("META_API_TOKEN")

metaapi = None

async def init_metaapi():
    global metaapi
    metaapi = MetaApi(META_API_TOKEN)
    # Await something to ensure the loop stays alive
    await asyncio.sleep(0.1)
