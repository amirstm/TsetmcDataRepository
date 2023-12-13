"""
Using the line implementation in this module, \
one can search through the instruments and add new instruments to the database.
"""
from dataclasses import dataclass
import logging
import httpx
from telegram_task import line
from tse_utils import tsetmc
from tse_utils_db.tse_market import (
    get_tse_market_session,
    InstrumentIdentification,
    InstrumentType,
    IndustrySector,
    IndustrySubSector,
    ExchangeMarket,
)


@dataclass
class JobDescription(line.JobDescription):
    """Overriden JobDescription for module tsetmc_instrument_searcher"""

    search_by: str = None
    do_recursive: bool = None


class TsetmcInstrumentSearcher(line.Worker):
    """Overriden worker for module tsetmc_instrument_searcher"""

    async def perform_task(self, job_description: JobDescription) -> line.JobReport:
        """Performs the task using the provided job description"""
        return await _Shift(
            job_description=job_description, logger=self._LOGGER
        ).perform_task()

    @classmethod
    def default_job_description(cls) -> JobDescription:
        """Creates the default job description for this worker"""
        return JobDescription(search_by="", do_recursive=True)


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
        new_search_results = self.filter_already_existing(search_results_filtered)
        new_identifications = await self.get_instrument_identifications(
            new_search_results
        )
        self.insert_to_identifications(new_identifications)
        return self.report

    def insert_to_identifications(
        self, new_identifications: list[tsetmc.InstrumentIdentification]
    ) -> None:
        """Inserts new records to database"""
        with get_tse_market_session() as session:
            instrument_types = session.query(InstrumentType).all()
            old_sectors = session.query(IndustrySector).all()
            old_sub_sectors = session.query(IndustrySubSector).all()
            old_exchange_markets = session.query(ExchangeMarket).all()
            unknown_type_instruments = [
                x
                for x in new_identifications
                if not any(
                    y for y in instrument_types if y.instrument_type_id == x.type_id
                )
            ]
            if unknown_type_instruments:
                set_unknown = {x.type_id for x in unknown_type_instruments}
                self.report.information.append(f"Unknown types ➡️ {set_unknown!r}")
                self.report.warnings.append(repr(unknown_type_instruments))
            instruments_to_add = [
                InstrumentIdentification(
                    isin=x.isin,
                    tsetmc_code=x.tsetmc_code,
                    name_persian=x.name_persian,
                    name_english=x.name_english,
                    ticker=x.ticker,
                    exchange_market_id=x.market_code,
                    industry_sub_sector_id=x.sub_sector_code,
                    instrument_type_id=x.type_id,
                )
                for x in new_identifications
                if any(y for y in instrument_types if y.instrument_type_id == x.type_id)
            ]
            session.add_all(self.get_new_sectors(new_identifications, old_sectors))
            session.add_all(
                self.get_new_sub_sectors(new_identifications, old_sub_sectors)
            )
            session.add_all(
                self.get_new_exchange_markets(new_identifications, old_exchange_markets)
            )
            session.add_all(instruments_to_add)
            session.commit()
            self.report.information.append(
                f"Inserted instruments ➡️ {len(instruments_to_add)}",
            )

    def get_new_exchange_markets(
        self,
        identifications: list[tsetmc.InstrumentIdentification],
        old_exchange_markets: list[ExchangeMarket],
    ) -> list[ExchangeMarket]:
        """Gets new exchange markets that should be added to the database"""
        all_exchange_markets: list[ExchangeMarket] = []
        for identification in identifications:
            if not any(
                x
                for x in all_exchange_markets
                if x.exchange_market_id == identification.market_code
            ):
                all_exchange_markets.append(
                    ExchangeMarket(
                        exchange_market_id=identification.market_code,
                        title=identification.market_title,
                    )
                )
        new_exchange_markets = [
            x
            for x in all_exchange_markets
            if not any(
                y
                for y in old_exchange_markets
                if y.exchange_market_id == x.exchange_market_id
            )
        ]
        self.report.information.append(
            f"Inserted exchange markets ➡️ {len(new_exchange_markets)}",
        )
        return new_exchange_markets

    def get_new_sub_sectors(
        self,
        identifications: list[tsetmc.InstrumentIdentification],
        old_sub_sectors: list[IndustrySubSector],
    ) -> list[IndustrySubSector]:
        """Gets new sub sectors that should be added to the database"""
        all_sub_sectors: list[IndustrySubSector] = []
        for identification in identifications:
            if not any(
                x
                for x in all_sub_sectors
                if x.industry_sub_sector_id == identification.sub_sector_code
            ):
                all_sub_sectors.append(
                    IndustrySubSector(
                        industry_sub_sector_id=identification.sub_sector_code,
                        title=identification.sub_sector_title,
                        industry_sector_id=identification.sector_code,
                    )
                )
        new_sub_sectors = [
            x
            for x in all_sub_sectors
            if not any(
                y
                for y in old_sub_sectors
                if y.industry_sub_sector_id == x.industry_sub_sector_id
            )
        ]
        self.report.information.append(
            f"Inserted sub sectors ➡️ {len(new_sub_sectors)}",
        )
        return new_sub_sectors

    def get_new_sectors(
        self,
        identifications: list[tsetmc.InstrumentIdentification],
        old_sectors: list[IndustrySector],
    ) -> list[IndustrySector]:
        """Gets new sectors that should be added to the database"""
        all_sectors: list[IndustrySector] = []
        for identification in identifications:
            if not any(
                x
                for x in all_sectors
                if x.industry_sector_id == identification.sector_code
            ):
                all_sectors.append(
                    IndustrySector(
                        industry_sector_id=identification.sector_code,
                        title=identification.sector_title,
                    )
                )
        new_sectors = [
            x
            for x in all_sectors
            if not any(
                y for y in old_sectors if y.industry_sector_id == x.industry_sector_id
            )
        ]
        self.report.information.append(
            f"Inserted sectors ➡️ {len(new_sectors)}",
        )
        return new_sectors

    async def get_instrument_identifications(
        self, search_results: list[tsetmc.InstrumentSearchItem]
    ) -> list[tsetmc.InstrumentIdentification]:
        """Gets identification from Tsetmc for new instruments"""
        results: list[tsetmc.InstrumentIdentification] = []
        async with tsetmc.TsetmcScraper() as scraper:
            for search_result in search_results:
                try:
                    self._logger.info(
                        "Getting instrument identity for [%s].",
                        repr(search_result),
                    )
                    instrument_identity = await scraper.get_instrument_identity(
                        tsetmc_code=search_result.tsetmc_code
                    )
                    results.append(instrument_identity)
                except (httpx.RequestError, tsetmc.TsetmcScrapeException):
                    self.report.warnings.append(
                        f"Getting instrument identity for [{search_result}] failed.",
                    )
        return results

    def filter_already_existing(
        self, search_results: list[tsetmc.InstrumentSearchItem]
    ) -> list[tsetmc.InstrumentSearchItem]:
        """Filters instruments that already exist on the database"""
        with get_tse_market_session() as session:
            tsetmc_codes = session.query(InstrumentIdentification).all()
        new_results = [
            x
            for x in search_results
            if not any(y for y in tsetmc_codes if y.tsetmc_code == x.tsetmc_code)
        ]
        self.report.information.append(
            f"New items ➡️ {len(new_results)}",
        )
        return new_results

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
        distinct_results.sort(key=lambda x: x.ticker)
        self._logger.info("Final filtered search results: %s", repr(distinct_results))
        self.report.information.append(
            f"Search results ➡️ {len(distinct_results)}",
        )
        return distinct_results

    async def search_and_process_tsetmc(
        self, search_by: str
    ) -> list[InstrumentIdentification]:
        """Search Tsetmc for instruments and processes the results"""
        search_results = await self.search_tsetmc(search_by)
        obsolete_count = len([x for x in search_results if not x.is_active])
        if (
            self.job_description.do_recursive
            and len(search_results) >= 40
            and obsolete_count == 0
        ):
            new_search_bys = {
                x.ticker[: len(search_by) + 1]
                for x in search_results
                if x.ticker.startswith(search_by) and len(x.ticker) > len(search_by)
            }
            for new_search_by in new_search_bys:
                search_results.extend(await self.search_tsetmc(search_by=new_search_by))
        return search_results

    async def search_tsetmc(self, search_by) -> list[tsetmc.InstrumentSearchItem]:
        """Searchs Tsetmc for instruments"""
        search_results: list[tsetmc.InstrumentSearchItem] = []
        async with tsetmc.TsetmcScraper() as scraper:
            try:
                self._logger.info("Searching for [%s]", search_by)
                search_results = await scraper.get_instrument_search(
                    search_value=search_by
                )
            except (httpx.RequestError, tsetmc.TsetmcScrapeException):
                self.report.warnings.append(
                    f"Searching for [{search_by}] failed.",
                )
        return search_results
