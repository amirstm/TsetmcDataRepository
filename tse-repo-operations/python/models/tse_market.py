"""This module holds the models for the tse_market database"""
from __future__ import annotations
from datetime import date, datetime
from typing import Optional
from dataclasses import dataclass
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import NCHAR, NVARCHAR, BIGINT
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import declarative_base


Base = declarative_base()


@dataclass
class IndustrySector(Base):
    """IndustrySector is used to identify the sector of an instrument"""
    __tablename__ = "industry_sector"

    industry_sector_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(NVARCHAR(64))

    industry_sub_sectors: Mapped[list[IndustrySubSector]] = relationship(
        back_populates="industry_sector", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"IndustrySector(id={self.industry_sector_id}, title={self.title})"


@dataclass
class IndustrySubSector(Base):
    """IndustrySubSector is a subset of IndustrySector"""
    __tablename__ = "industry_sub_sector"

    industry_sub_sector_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(NVARCHAR(64))
    industry_sector_id: Mapped[int] = mapped_column(
        ForeignKey("industry_sector.industry_sector_id")
    )

    industry_sector: Mapped[IndustrySector] = relationship(
    )
    instrument_identifications: Mapped[list[InstrumentIdentification]] = relationship(
        back_populates="industry_sub_sector", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"IndustrySubSector(id={self.industry_sub_sector_id}, \
title={self.title}, industry_sector={self.industry_sector})"


@dataclass
class ExchangeMarket(Base):
    """Identifies the exchange in which the instrument is traded"""
    __tablename__ = "exchange_market"

    exchange_market_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(NVARCHAR(64))

    instrument_identifications: Mapped[list[InstrumentIdentification]] = relationship(
        back_populates="exchange_market", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"ExchangeMarket(id={self.exchange_market_id}, title={self.title})"


@dataclass
class InstrumentType(Base):
    """Instruments are of different types and this table is used for that purpose"""
    __tablename__ = "instrument_type"

    instrument_type_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(NVARCHAR(128))

    instrument_identifications: Mapped[list[InstrumentIdentification]] = relationship(
        back_populates="instrument_type", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"InstrumentType(id={self.instrument_type_id}, title={self.title})"


@dataclass
class InstrumentIdentification(Base):
    """Holds the identification of an instrument"""
    __tablename__ = "instrument_identification"

    isin: Mapped[str] = mapped_column(NCHAR(12), primary_key=True)
    tsetmc_code: Mapped[str] = mapped_column(NVARCHAR(32))
    ticker: Mapped[str] = mapped_column(NVARCHAR(32))
    persian_name: Mapped[Optional[str]] = mapped_column(NVARCHAR(64))
    english_name: Mapped[Optional[str]] = mapped_column(NVARCHAR(64))
    instrument_type_id: Mapped[int] = mapped_column(
        ForeignKey("instrument_type.instrument_type_id")
    )
    industry_sub_sector_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("industry_sub_sector.industry_sub_sector_id")
    )
    exchange_market_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("exchange_market.exchange_market_id")
    )

    instrument_type: Mapped[InstrumentType] = relationship(
    )
    industry_sub_sector: Mapped[IndustrySubSector] = relationship(
    )
    exchange_market: Mapped[ExchangeMarket] = relationship(
    )


@dataclass
class IndexIdentification(Base):
    """Holds the identification of an index"""
    __tablename__ = "index_identification"

    isin: Mapped[str] = mapped_column(NCHAR(12), primary_key=True)
    tsetmc_code: Mapped[str] = mapped_column(NVARCHAR(32))
    persian_name: Mapped[Optional[str]] = mapped_column(NVARCHAR(64))
    english_name: Mapped[Optional[str]] = mapped_column(NVARCHAR(64))


@dataclass
class DailyTradeCandle(Base):
    """Historical daily trade candles"""
    __tablename__ = "daily_trade_candle"

    daily_trade_candle_id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    isin: Mapped[str] = mapped_column(
        ForeignKey("instrument_identification.isin")
    )
    record_date: Mapped[date] = mapped_column()
    previous_price: Mapped[int] = mapped_column(BIGINT())
    open_price: Mapped[int] = mapped_column(BIGINT())
    close_price: Mapped[int] = mapped_column(BIGINT())
    last_price: Mapped[int] = mapped_column(BIGINT())
    max_price: Mapped[int] = mapped_column(BIGINT())
    min_price: Mapped[int] = mapped_column(BIGINT())
    trade_num: Mapped[int] = mapped_column()
    trade_volume: Mapped[int] = mapped_column(BIGINT())
    trade_value: Mapped[int] = mapped_column(BIGINT())

    instrument_identification: Mapped[InstrumentIdentification] = relationship(
    )


@dataclass
class DailyClientType(Base):
    """Historical daily client types"""
    __tablename__ = "daily_client_type"

    daily_client_type_id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    isin: Mapped[str] = mapped_column(
        ForeignKey("instrument_identification.isin")
    )
    record_date: Mapped[date] = mapped_column()
    natural_buy_num: Mapped[int] = mapped_column()
    legal_buy_num: Mapped[int] = mapped_column()
    natural_buy_value: Mapped[int] = mapped_column(BIGINT())
    legal_buy_value: Mapped[int] = mapped_column(BIGINT())
    natural_buy_volume: Mapped[int] = mapped_column(BIGINT())
    legal_buy_volume: Mapped[int] = mapped_column(BIGINT())
    natural_sell_num: Mapped[int] = mapped_column()
    legal_sell_num: Mapped[int] = mapped_column()
    natural_sell_value: Mapped[int] = mapped_column(BIGINT())
    legal_sell_value: Mapped[int] = mapped_column(BIGINT())
    natural_sell_volume: Mapped[int] = mapped_column(BIGINT())
    legal_sell_volume: Mapped[int] = mapped_column(BIGINT())

    instrument_identification: Mapped[InstrumentIdentification] = relationship(
    )


@dataclass
class DailyInstrumentDetail(Base):
    """Historical daily instrument details"""
    __tablename__ = "daily_instrument_detail"

    daily_instrument_detail_id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    isin: Mapped[str] = mapped_column(
        ForeignKey("instrument_identification.isin")
    )
    record_date: Mapped[date] = mapped_column()
    total_share_count: Mapped[int] = mapped_column(BIGINT())
    base_volume: Mapped[int] = mapped_column(BIGINT())
    max_price_threshold: Mapped[int] = mapped_column(BIGINT())
    min_price_threshold: Mapped[int] = mapped_column(BIGINT())

    instrument_identification: Mapped[InstrumentIdentification] = relationship(
    )


@dataclass
class TickTrade(Base):
    """The historical microtrades of an instrument"""
    __tablename__ = "tick_trade"

    tick_trade_id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    isin: Mapped[str] = mapped_column(
        ForeignKey("instrument_identification.isin")
    )
    record_date_time: Mapped[datetime] = mapped_column()
    htn: Mapped[int] = mapped_column()
    quantity: Mapped[int] = mapped_column(BIGINT())
    price: Mapped[int] = mapped_column(BIGINT())
    invalidated: Mapped[bool] = mapped_column(default=False)

    instrument_identification: Mapped[InstrumentIdentification] = relationship(
    )


@dataclass
class DailyIndexValue(Base):
    """Value of an index historically in a daily period"""
    __tablename__ = "daily_index_value"

    daily_index_value_id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    isin: Mapped[str] = mapped_column(
        ForeignKey("instrument_identification.isin")
    )
    record_date: Mapped[date] = mapped_column()
    close_value: Mapped[float] = mapped_column()
    max_value: Mapped[float] = mapped_column()
    min_value: Mapped[float] = mapped_column()

    instrument_identification: Mapped[InstrumentIdentification] = relationship(
    )
