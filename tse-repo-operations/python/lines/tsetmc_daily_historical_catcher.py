"""
Using the line implementation in this module, \
one can fetch daily historical data from TSETMC.
"""
from dataclasses import dataclass
import logging
import sqlalchemy
from telegram_task import line
from tse_utils import tsetmc
from models.tse_market import (
    get_tse_market_session,
    InstrumentIdentification,
    DailyTradeCandle
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
            job_description=job_description,
            logger=self._LOGGER
        ).perform_task()

    @classmethod
    def default_job_description(cls) -> JobDescription:
        """Creates the default job description for this worker"""
        return JobDescription(
            get_trade_data=True,
            get_client_type_data=True,
            specific_instrument_identifier=None
        )


class _Shift:
    """Internal class for simpler performance of the worker's task"""
    _update_chunk_len: int = 10000

    def __init__(
            self,
            job_description: JobDescription,
            logger: logging.Logger
    ):
        self._LOGGER: logging.Logger = logger
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
        await self.__update_trade_data(instruments)
        return self.report

    async def __update_trade_data(
            self,
            instruments: list[InstrumentIdentification]
    ):
        """Gets and updates trade data"""
        max_record_dates = self.__get_max_record_dates()
        success = 0
        failure = 0
        new_batch_data = []
        async with tsetmc.TsetmcScraper() as scaper:
            for instrument in instruments:
                previous_last_record = next(
                    (
                        x
                        for x in max_record_dates
                        if x.isin == instrument.isin
                    ),
                    None
                )
                try:
                    self._LOGGER.info(
                        "Catching trade data for %s",
                        repr(instrument)
                    )
                    trade_data = await scaper.get_closing_price_daily_list(
                        tsetmc_code=instrument.tsetmc_code
                    )
                    success += 1
                except:
                    self._LOGGER.error(
                        "Catching trade data failed for %s",
                        repr(instrument)
                    )
                    failure += 1
                    continue
                new_data = [
                    x
                    for x in trade_data
                    if x.last_trade_datetime.date() > previous_last_record.record_date
                ] if previous_last_record else trade_data
                print(len(new_data))
                new_batch_data.extend([
                    DailyTradeCandle(
                        isin=instrument.isin,
                        record_date=x.last_trade_datetime.date(),
                        previous_price=x.previous_price,
                        open_price=x.open_price,
                        max_price=x.max_price,
                        min_price=x.min_price,
                        close_price=x.close_price,
                        last_price=x.last_price,
                        trade_num=x.trade_num,
                        trade_value=x.trade_value,
                        trade_volume=x.trade_volume
                    )
                    for x in new_data
                ])
                break
        if new_batch_data:
            self.insert_trade_batch_in_database(new_batch_data)

    def insert_trade_batch_in_database(
            self,
            new_batch_data: list[DailyTradeCandle]
    ) -> None:
        """Inserts a batch of trade data into database"""
        with get_tse_market_session() as session:
            session.add_all(new_batch_data)
            self._LOGGER.info(
                "Inserting %d DailyTradeCandle rows into database.",
                len(new_batch_data)
            )
            session.commit()

    def __get_max_record_dates(self) -> list[DailyTradeCandle]:
        """Gets max previous record date for each instrument"""
        with get_tse_market_session() as session:
            subq = session.query(
                DailyTradeCandle.isin,
                sqlalchemy.func.max(
                    DailyTradeCandle.record_date
                ).label('maxdate')
            ).group_by(DailyTradeCandle.isin).subquery('t2')
            query = session.query(DailyTradeCandle).join(
                subq,
                sqlalchemy.and_(
                    DailyTradeCandle.isin == subq.c.isin,
                    DailyTradeCandle.record_date == subq.c.maxdate
                )
            )
            max_record_dates = query.all()
        return max_record_dates

    @classmethod
    def get_instruments(
        cls,
        search_by: str
    ) -> list[InstrumentIdentification]:
        """List instruments according to the search_by identifier"""
        with get_tse_market_session() as session:
            if search_by:
                return session.query(InstrumentIdentification).filter(
                    sqlalchemy.or_(
                        InstrumentIdentification.isin == search_by,
                        InstrumentIdentification.ticker.contains(search_by)
                    )).all()
            else:
                return session.query(InstrumentIdentification).all()
