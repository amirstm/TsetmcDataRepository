from __future__ import annotations
import os
from datetime import date, datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.tse_market import InstrumentType, get_tse_market_session
from tse_utils.tse_client import TseClientScraper
import asyncio


async def main():
    async with TseClientScraper() as tse_client:
        instruments, indices = await tse_client.get_instruments_list()
    print(instruments)

if __name__ == "__main__":
    asyncio.run(main())
