from __future__ import annotations
from dataclasses import dataclass
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from typing import Optional
from sqlalchemy.types import NCHAR, NVARCHAR
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import mapper, sessionmaker
from dotenv import load_dotenv
import os

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


Base = declarative_base()

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


@dataclass
class IndustrySector(Base):
    __tablename__ = "industry_sector"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(NVARCHAR(64))

    industry_sub_sectors: Mapped[list[IndustrySubSector]] = relationship(
        back_populates="industry_sector", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"IndustrySector(id={self.id}, title={self.title})"


@dataclass
class IndustrySubSector(Base):
    __tablename__ = "industry_sub_sector"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(NVARCHAR(64))
    industry_sector_id: Mapped[int] = mapped_column(
        ForeignKey("industry_sector.id")
    )

    industry_sector: Mapped[IndustrySector] = relationship(
    )
    instrument_identifications: Mapped[list[InstrumentIdentification]] = relationship(
        back_populates="industry_sub_sector", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"IndustrySubSector(id={self.id}, title={self.title}, \
industry_sector={self.industry_sector})"


@dataclass
class ExchangeMarket(Base):
    __tablename__ = "exchange_market"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(NVARCHAR(64))

    instrument_identifications: Mapped[list[InstrumentIdentification]] = relationship(
        back_populates="exchange_market", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"ExchangeMarket(id={self.id}, title={self.title})"


@dataclass
class InstrumentType(Base):
    __tablename__ = "instrument_type"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(NVARCHAR(128))

    instrument_identifications: Mapped[list[InstrumentIdentification]] = relationship(
        back_populates="instrument_type", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"InstrumentType(id={self.id}, title={self.title})"


@dataclass
class InstrumentIdentification(Base):
    __tablename__ = "instrument_identification"

    isin: Mapped[str] = mapped_column(NCHAR(12), primary_key=True)
    tsetmc_code: Mapped[str] = mapped_column(NVARCHAR(32))
    ticker: Mapped[str] = mapped_column(NVARCHAR(32))
    persian_name: Mapped[Optional[str]] = mapped_column(NVARCHAR(64))
    english_name: Mapped[Optional[str]] = mapped_column(NVARCHAR(64))
    instrument_type_id: Mapped[int] = mapped_column(
        ForeignKey("instrument_type.id")
    )
    industry_sub_sector_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("industry_sub_sector.id")
    )
    exchange_market_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("exchange_market.id")
    )

    instrument_type: Mapped[InstrumentType] = relationship(
    )
    industry_sub_sector: Mapped[IndustrySubSector] = relationship(
    )
    exchange_market: Mapped[ExchangeMarket] = relationship(
    )


@dataclass
class IndexIdentification(Base):
    __tablename__ = "index_identification"

    isin: Mapped[str] = mapped_column(NCHAR(12), primary_key=True)
    tsetmc_code: Mapped[str] = mapped_column(NVARCHAR(32))
    persian_name: Mapped[Optional[str]] = mapped_column(NVARCHAR(64))
    english_name: Mapped[Optional[str]] = mapped_column(NVARCHAR(64))


def loadSession():
    """"""

    Session = sessionmaker(bind=engine)
    session = Session()
    return session


if __name__ == "__main__":
    session = loadSession()
    # res = session.query(InstrumentType).all()
    # print(res[0])
    # res = session.query(InstrumentIdentification).all()
    # print(res[0])
    res = session.query(InstrumentType).where(
        InstrumentType.id == 12345).first()
    print(res.instrument_identifications)
