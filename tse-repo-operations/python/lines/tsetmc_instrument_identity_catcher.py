"""
Using the line implementation in this module, \
one can update the instrument identity data from TSETMC.
"""
from typing import Callable
from dataclasses import dataclass
from datetime import date
from telegram_task import line
from tse_utils import tsetmc
from utils.persian_arabic import arabic_to_persian
from models.tse_market import (
    get_tse_market_session,
    InstrumentIdentification,
    IndustrySector,
    IndustrySubSector
)


@dataclass
class JobDescription(line.JobDescription):
    """Overriden JobDescription for module tsetmc_instrument_identity"""
    search_by: str = None


class TsetmcInstrumentIdentityCatcher(line.Worker):
    """Overriden worker for module tsetmc_instrument_identity"""

    async def perform_task(self, job_description: JobDescription) -> line.JobReport:
        """Performs the task using the provided job description"""
        return await _Shift(job_description=job_description).perform_task()

    @classmethod
    def default_job_description(cls) -> JobDescription:
        """Creates the default job description for this worker"""
        return JobDescription(
            search_by=""
        )


class _Shift:
    """Internal class for simpler performance of the worker's task"""

    def __init__(self, job_description: JobDescription):
        self.job_description: JobDescription = job_description
        self.report: line.JobReport = line.JobReport()

    async def perform_task(self) -> line.JobReport:
        matched_instruments = self.match_instruments(
            self.job_description.search_by
        )
        """Performs the task using the provided job description"""
        match len(matched_instruments):
            case 0:
                raise line.TaskException(
                    message="No instruments were matched with your search parameter."
                )
            case 1:
                self.update_instrument_from_tsetmc(matched_instruments[0])
            case _:
                raise line.TaskException(
                    message="Multiple instruments were matched with your search parameter.",
                    html_message=f"""\
Multiple instruments were matched with your search parameter. Please choose one.
{"\n".join([
                        tsetmc.ticker_with_tsetmc_homepage_link(
                            ticker=x.ticker,
                            tsetmc_code=x.tsetmc_code
                        ) + ": " + x.isin
                        for x in matched_instruments
                    ])}
"""
                )
        return self.report

    def update_instrument_from_tsetmc(
            self,
            instrument: InstrumentIdentification
    ) -> None:
        """
        After a single instrument has been matched, \
        this method will fetch and update that instrument's data
        """

    @classmethod
    def match_instruments(
            cls,
            search_by: str
    ) -> list[InstrumentIdentification]:
        """Matches the instruments from database with search_by input"""
        with get_tse_market_session() as session:
            by_isin = session.query(InstrumentIdentification).where(
                InstrumentIdentification.isin == search_by
            ).first()
            if by_isin:
                return [by_isin]
            by_ticker = session.query(InstrumentIdentification).where(
                InstrumentIdentification.ticker == search_by
            ).all()
            return by_ticker
