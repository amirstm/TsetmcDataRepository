from __future__ import annotations
from dataclasses import dataclass
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from typing import Optional
from sqlalchemy.types import NCHAR, NVARCHAR, BIGINT
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import mapper, sessionmaker
from dotenv import load_dotenv
import os
from datetime import date, datetime
from models.tse_market import InstrumentType

load_dotenv()

PROXY_URL = os.getenv('PROXY_URL')
PROXY_URL = PROXY_URL if PROXY_URL else None
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_DB = os.getenv("MYSQL_DB")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")


mysql_connector = "mysql+mysqlconnector://{}:{}@{}:{}/{}".format(
    MYSQL_USER,
    MYSQL_PASSWORD,
    MYSQL_HOST,
    MYSQL_PORT,
    MYSQL_DB
)
engine = create_engine(
    mysql_connector,
    echo=False
)


if __name__ == "__main__":
    # res = session.query(InstrumentType).all()
    # print(res[0])
    # res = session.query(InstrumentIdentification).all()
    # print(res[0])
    with sessionmaker(bind=engine)() as session:
        res = session.query(InstrumentType).where(
            InstrumentType.instrument_type_id == 12345).first()
        print(res.instrument_identifications)
