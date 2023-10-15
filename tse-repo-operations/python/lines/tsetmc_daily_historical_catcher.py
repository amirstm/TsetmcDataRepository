"""
Using the line implementation in this module, \
one can fetch daily historical data from TSETMC.
"""
from dataclasses import dataclass
import logging
import httpx
import sqlalchemy
from telegram_task import line
from tse_utils import tsetmc
from models.tse_market import (
    get_tse_market_session,
    InstrumentIdentification,
    DailyTradeCandle,
    DailyClientType,
)


@dataclass
class JobDescription(line.JobDescription):
    """Overriden JobDescription for module tsetmc_daily_historical_catcher"""

    get_trade_data: bool = None
    get_client_type_data: bool = None
    specific_instrument_identifier: str = None


class TsetmcDailyHistoricalCatcher(line.Worker):
    """Overriden worker for module tsetmc_daily_historical_catcher"""

    async def perform_task(self, job_description: JobDescription) -> line.JobReport:
        """Performs the task using the provided job description"""
        return await _Shift(
            job_description=job_description, logger=self._LOGGER
        ).perform_task()

    @classmethod
    def default_job_description(cls) -> JobDescription:
        """Creates the default job description for this worker"""
        return JobDescription(
            get_trade_data=True,
            get_client_type_data=True,
            specific_instrument_identifier=None,
        )


class _Shift:
    """Internal class for simpler performance of the worker's task"""

    _update_chunk_len: int = 10000

    def __init__(self, job_description: JobDescription, logger: logging.Logger):
        self._logger: logging.Logger = logger
        self.job_description: JobDescription = job_description
        self.report: line.JobReport = line.JobReport()

    async def perform_task(self) -> line.JobReport:
        """Performs the task using the provided job description"""
        instruments = self.get_instruments(
            search_by=self.job_description.specific_instrument_identifier
        )
        self.report.information.append(
            f"Instruments count ➡️ {len(instruments)}",
        )
        if self.job_description.get_trade_data:
            await self.__update_trade_data(instruments)
        if self.job_description.get_client_type_data:
            await self.__update_client_type_data(instruments)
        return self.report

    async def __update_client_type_data(
        self, instruments: list[InstrumentIdentification]
    ):
        """Gets and updates client type data"""
        max_record_dates = self.__get_max_client_type_data_dates()
        success = 0
        failure = 0
        client_type_data_inserted = 0
        new_batch_data = []
        async with tsetmc.TsetmcScraper() as scaper:
            for instrument in instruments:
                previous_last_record = next(
                    (x for x in max_record_dates if x.isin == instrument.isin), None
                )
                try:
                    self._logger.info(
                        "Catching client type data for %s", repr(instrument)
                    )
                    client_type_data = await scaper.get_client_type_daily_list(
                        tsetmc_code=instrument.tsetmc_code
                    )
                    success += 1
                except (httpx.RequestError, tsetmc.TsetmcScrapeException):
                    self._logger.error(
                        "Catching client type data failed for %s", repr(instrument)
                    )
                    failure += 1
                    continue
                new_data = [
                    self.client_type_data_tsetmc_to_db(
                        isin=instrument.isin, tsetmc_data=x
                    )
                    for x in client_type_data
                    if x.trade_volume() > 0
                    and (
                        previous_last_record is None
                        or x.record_date > previous_last_record.record_date
                    )
                ]
                new_batch_data.extend(new_data)
                if len(new_batch_data) > self._update_chunk_len:
                    client_type_data_inserted += self.insert_trade_batch_in_database(
                        new_batch_data
                    )
            if new_batch_data:
                client_type_data_inserted += self.insert_trade_batch_in_database(
                    new_batch_data
                )
        self.report.information.extend(
            [
                f"Client type inserted ➡️ {client_type_data_inserted}",
                f"Client type catch success ➡️ {success}",
                f"Client type catch failure ➡️ {failure}",
            ]
        )

    async def __update_trade_data(self, instruments: list[InstrumentIdentification]):
        """Gets and updates trade data"""
        max_record_dates = self.__get_max_trade_data_dates()
        success = 0
        failure = 0
        trade_data_inserted = 0
        new_batch_data = []
        async with tsetmc.TsetmcScraper() as scaper:
            for instrument in instruments:
                previous_last_record = next(
                    (x for x in max_record_dates if x.isin == instrument.isin), None
                )
                try:
                    self._logger.info("Catching trade data for %s", repr(instrument))
                    trade_data = await scaper.get_closing_price_daily_list(
                        tsetmc_code=instrument.tsetmc_code
                    )
                    success += 1
                except (httpx.RequestError, tsetmc.TsetmcScrapeException):
                    self._logger.error(
                        "Catching trade data failed for %s", repr(instrument)
                    )
                    failure += 1
                    continue
                new_data = [
                    self.trade_data_tsetmc_to_db(isin=instrument.isin, tsetmc_data=x)
                    for x in trade_data
                    if x.trade_volume > 0
                    and (
                        previous_last_record is None
                        or x.last_trade_datetime.date()
                        > previous_last_record.record_date
                    )
                ]
                new_batch_data.extend(new_data)
                if len(new_batch_data) > self._update_chunk_len:
                    trade_data_inserted += self.insert_trade_batch_in_database(
                        new_batch_data
                    )
            if new_batch_data:
                trade_data_inserted += self.insert_trade_batch_in_database(
                    new_batch_data
                )
        self.report.information.extend(
            [
                f"Trade data inserted ➡️ {trade_data_inserted}",
                f"Trade catch success ➡️ {success}",
                f"Trade catch failure ➡️ {failure}",
            ]
        )

    @classmethod
    def client_type_data_tsetmc_to_db(
        cls, isin: str, tsetmc_data: tsetmc.ClientTypeDaily
    ) -> DailyClientType:
        """Converts Tsetmc trade data to database model"""
        return DailyClientType(
            isin=isin,
            record_date=tsetmc_data.record_date,
            legal_buy_num=tsetmc_data.legal.buy.num,
            legal_buy_value=tsetmc_data.legal.buy.value,
            legal_buy_volume=tsetmc_data.legal.buy.volume,
            legal_sell_num=tsetmc_data.legal.sell.num,
            legal_sell_value=tsetmc_data.legal.sell.value,
            legal_sell_volume=tsetmc_data.legal.sell.volume,
            natural_buy_num=tsetmc_data.natural.buy.num,
            natural_buy_value=tsetmc_data.natural.buy.value,
            natural_buy_volume=tsetmc_data.natural.buy.volume,
            natural_sell_num=tsetmc_data.natural.sell.num,
            natural_sell_value=tsetmc_data.natural.sell.value,
            natural_sell_volume=tsetmc_data.natural.sell.volume,
        )

    @classmethod
    def trade_data_tsetmc_to_db(
        cls, isin: str, tsetmc_data: tsetmc.ClosingPriceDaily
    ) -> DailyTradeCandle:
        """Converts Tsetmc trade data to database model"""
        return DailyTradeCandle(
            isin=isin,
            record_date=tsetmc_data.last_trade_datetime.date(),
            previous_price=tsetmc_data.previous_price,
            open_price=tsetmc_data.open_price,
            max_price=tsetmc_data.max_price,
            min_price=tsetmc_data.min_price,
            close_price=tsetmc_data.close_price,
            last_price=tsetmc_data.last_price,
            trade_num=tsetmc_data.trade_num,
            trade_value=tsetmc_data.trade_value,
            trade_volume=tsetmc_data.trade_volume,
        )

    def insert_trade_batch_in_database(
        self, new_batch_data: list[DailyTradeCandle]
    ) -> int:
        """Inserts a batch of trade data into database"""
        with get_tse_market_session() as session:
            session.add_all(new_batch_data)
            self._logger.info(
                "Inserting %d DailyTradeCandle rows into database.", len(new_batch_data)
            )
            row_num = len(new_batch_data)
            session.commit()
            new_batch_data.clear()
            return row_num

    def __get_max_client_type_data_dates(self) -> list[DailyClientType]:
        """Gets max previous record date of client type data for each instrument"""
        with get_tse_market_session() as session:
            # pylint: disable=not-callable
            # sqlalchemy.func.max is indeed callable
            subq = (
                session.query(
                    DailyClientType.isin,
                    sqlalchemy.func.max(DailyClientType.record_date).label("maxdate"),
                )
                .group_by(DailyClientType.isin)
                .subquery("t2")
            )
            query = session.query(DailyClientType).join(
                subq,
                sqlalchemy.and_(
                    DailyClientType.isin == subq.c.isin,
                    DailyClientType.record_date == subq.c.maxdate,
                ),
            )
            max_record_dates = query.all()
        return max_record_dates

    def __get_max_trade_data_dates(self) -> list[DailyTradeCandle]:
        """Gets max previous record date of trade data for each instrument"""
        with get_tse_market_session() as session:
            # pylint: disable=not-callable
            # sqlalchemy.func.max is indeed callable
            subq = (
                session.query(
                    DailyTradeCandle.isin,
                    sqlalchemy.func.max(DailyTradeCandle.record_date).label("maxdate"),
                )
                .group_by(DailyTradeCandle.isin)
                .subquery("t2")
            )
            query = session.query(DailyTradeCandle).join(
                subq,
                sqlalchemy.and_(
                    DailyTradeCandle.isin == subq.c.isin,
                    DailyTradeCandle.record_date == subq.c.maxdate,
                ),
            )
            max_record_dates = query.all()
        return max_record_dates

    @classmethod
    def get_instruments(cls, search_by: str) -> list[InstrumentIdentification]:
        """List instruments according to the search_by identifier"""
        with get_tse_market_session() as session:
            if search_by:
                return (
                    session.query(InstrumentIdentification)
                    .filter(
                        sqlalchemy.or_(
                            InstrumentIdentification.isin == search_by,
                            InstrumentIdentification.ticker.contains(search_by),
                        )
                    )
                    .all()
                )
            return session.query(InstrumentIdentification).all()
