"""
Using the line implementation in this module, \
one can update the instrument identity data from TSETMC.
"""
from typing import Callable
from dataclasses import dataclass
from datetime import date
from telegram_task import line
import tse_utils.tsetmc as tsetmc
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


class TsetmcInstrumentIdentity(line.Worker):
    """Overriden worker for module tsetmc_instrument_identity"""

    async def perform_task(self, job_description: JobDescription) -> line.JobReport:
        """Performs the task using the provided job description"""
        return _Shift(job_description=job_description).perform_task()


class _Shift:
    """Internal class for simpler performance of the worker's task"""

    def __init__(self, job_description: JobDescription):
        self.job_description: JobDescription = job_description
        self.report: line.JobReport = line.JobReport()

    def perform_task(self) -> line.JobReport:

        return self.report
