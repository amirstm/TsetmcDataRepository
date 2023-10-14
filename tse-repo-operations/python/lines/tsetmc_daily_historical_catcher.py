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

        return self.report

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
