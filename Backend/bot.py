import asyncio
from metaapi_connector import init_metaapi, metaapi

async def main():
    await init_metaapi()
    # continue your strategy setup here...

if __name__ == '__main__':
    asyncio.run(main())
