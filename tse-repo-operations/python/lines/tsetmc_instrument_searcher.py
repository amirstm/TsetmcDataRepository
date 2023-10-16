"""
Using the line implementation in this module, \
one can search through the instruments and add new instruments to the database.
"""
from dataclasses import dataclass
import logging
import httpx
from sqlalchemy.orm import Session
from telegram_task import line
from tse_utils import tsetmc
from models.tse_market import (
    get_tse_market_session,
    InstrumentIdentification,
    InstrumentType,
)


@dataclass
class JobDescription(line.JobDescription):
    """Overriden JobDescription for module tsetmc_instrument_searcher"""

    search_by: str = None
    do_recursive: bool = None


class TsetmcInstrumentIdentityCatcher(line.Worker):
    """Overriden worker for module tsetmc_instrument_searcher"""

    async def perform_task(self, job_description: JobDescription) -> line.JobReport:
        """Performs the task using the provided job description"""
        return await _Shift(
            job_description=job_description, logger=self._LOGGER
        ).perform_task()

    @classmethod
    def default_job_description(cls) -> JobDescription:
        """Creates the default job description for this worker"""
        return JobDescription(search_by="", do_recursive=False)


class _Shift:
    """Internal class for simpler performance of the worker's task"""

    def __init__(self, job_description: JobDescription, logger: logging.Logger):
        self._logger: logging.Logger = logger
        self.job_description: JobDescription = job_description
        self.report: line.JobReport = line.JobReport()

    async def perform_task(self) -> line.JobReport:
        """Performs the task using the provided job description"""
        search_results = await self.search_and_process_tsetmc(
            self.job_description.search_by
        )
        search_results_filtered = self.clean_up_search_results(search_results)

    def clean_up_search_results(
        self, search_results: list[tsetmc.InstrumentSearchItem]
    ) -> list[tsetmc.InstrumentSearchItem]:
        """Cleans up redundant and obsolete data from search results"""
        results = [x for x in search_results if x.is_active]
        seen = set()
        distinct_results = [
            p
            for p in results
            if p.tsetmc_code not in seen and not seen.add(p.tsetmc_code)
        ]
        distinct_results.sort(key=lambda x: x.index)

    async def search_and_process_tsetmc(
        self, search_by: str
    ) -> list[InstrumentIdentification]:
        """Search Tsetmc for instruments and processes the results"""
        search_results = await self.search_tsetmc(search_by)
        obsolete_count = len([x for x in search_results if not x.is_active])
        if len(search_results) >= 40 and obsolete_count == 0:
            new_search_bys = set(
                [
                    x.ticker[: len(search_by) + 1]
                    for x in search_results
                    if x.ticker.startswith(search_by) and len(x.ticker) > len(search_by)
                ]
            )
            for new_search_by in new_search_bys:
                search_results.extend(await self.search_tsetmc(search_by=new_search_by))
        return search_results

    async def search_tsetmc(self, search_by) -> list[tsetmc.InstrumentSearchItem]:
        """Searchs Tsetmc for instruments"""
        search_results: list[tsetmc.InstrumentSearchItem] = []
        async with tsetmc.TsetmcScraper() as scraper:
            try:
                self._LOGGER.error("Searching for [%s]", search_by)
                search_results = await scraper.get_instrument_search(
                    search_value=search_by
                )
            except (httpx.RequestError, tsetmc.TsetmcScrapeException):
                self._LOGGER.error("Searching for [%s] failed.", search_by)
        return search_results
