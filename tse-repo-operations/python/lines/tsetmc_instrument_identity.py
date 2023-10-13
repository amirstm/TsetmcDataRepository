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
