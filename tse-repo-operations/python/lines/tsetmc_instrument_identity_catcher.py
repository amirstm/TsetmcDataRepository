"""
Using the line implementation in this module, \
one can update the instrument identity data from TSETMC.
"""
from dataclasses import dataclass
import logging
import httpx
from sqlalchemy.orm import Session
from telegram_task import line
from tse_utils import tsetmc
from tse_utils_db.tse_market import (
    get_tse_market_session,
    InstrumentIdentification,
    IndustrySector,
    IndustrySubSector,
    ExchangeMarket
)


@dataclass
class JobDescription(line.JobDescription):
    """Overriden JobDescription for module tsetmc_instrument_identity_catcher"""
    search_by: str = None


class TsetmcInstrumentIdentityCatcher(line.Worker):
    """Overriden worker for module tsetmc_instrument_identity_catcher"""

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
            search_by=""
        )


class _Shift:
    """Internal class for simpler performance of the worker's task"""

    def __init__(
            self,
            job_description: JobDescription,
            logger: logging.Logger
    ):
        self._logger: logging.Logger = logger
        self.job_description: JobDescription = job_description
        self.report: line.JobReport = line.JobReport()

    async def perform_task(self) -> line.JobReport:
        """Performs the task using the provided job description"""
        matched_instruments = self.match_instruments(
            self.job_description.search_by
        )
        match len(matched_instruments):
            case 0:
                raise line.TaskException(
                    message="No instruments were matched with your search parameter."
                )
            case 1:
                await self.__update_instrument_from_tsetmc(matched_instruments[0])
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
        self.add_updated_instrument_to_report(isin=matched_instruments[0].isin)
        return self.report

    def add_updated_instrument_to_report(self, isin: str):
        """Adds updated instrument data to report"""
        with get_tse_market_session() as session:
            instrument = session.query(InstrumentIdentification).where(
                InstrumentIdentification.isin == isin
            ).first()
            self.report.information.extend([
                f"Instrument ➡️ {tsetmc.ticker_with_tsetmc_homepage_link(
                    ticker=instrument.ticker,
                    tsetmc_code=instrument.tsetmc_code
                )}",
                f"Isin ➡️ {instrument.isin}",
                f"Tsetmc Code ➡️ {instrument.tsetmc_code}",
                f"Persian Name ➡️ {instrument.name_persian}",
                f"English Name ➡️ {instrument.name_english}",
                f"Industry ➡️ {
                    instrument.industry_sub_sector.title
                    if instrument.industry_sub_sector
                    else None
                }",
                f"Exchange ➡️ {
                    instrument.exchange_market.title
                    if instrument.exchange_market
                    else None
                }"
            ])

    async def __update_instrument_from_tsetmc(
            self,
            instrument: InstrumentIdentification
    ) -> None:
        """
        After a single instrument has been matched, \
        this method will fetch and update that instrument's data
        """
        tsetmc_identity = await self.__get_instrument_identity(instrument)
        with get_tse_market_session() as session:
            self.__handle_industry(tsetmc_identity, session)
            self.__handle_exchange_market(tsetmc_identity, session)
            db_instrument = session.query(InstrumentIdentification).where(
                InstrumentIdentification.isin == instrument.isin
            ).first()
            db_instrument.industry_sub_sector_id = tsetmc_identity.sub_sector_code
            db_instrument.exchange_market_id = tsetmc_identity.market_code
            session.commit()

    def __handle_exchange_market(
        self,
            tsetmc_identity: tsetmc.InstrumentIdentification,
            session: Session
    ) -> None:
        """Checks if exchange market needs to be updated on database"""
        current_exchange = session.query(ExchangeMarket).where(
            ExchangeMarket.exchange_market_id == tsetmc_identity.market_code
        ).first()
        if not current_exchange:
            self._logger.info(
                "Adding exchange [%d]: [%s] to database.",
                tsetmc_identity.market_code,
                tsetmc_identity.market_title
            )
            session.add(ExchangeMarket(
                exchange_market_id=tsetmc_identity.market_code,
                title=tsetmc_identity.market_title
            ))

    def __handle_industry(
            self,
            tsetmc_identity: tsetmc.InstrumentIdentification,
            session: Session
    ) -> None:
        """Checks if industry needs to be updated on database"""
        current_sector = session.query(IndustrySector).where(
            IndustrySector.industry_sector_id == tsetmc_identity.sector_code
        ).first()
        if not current_sector:
            self._logger.info(
                "Adding sector [%d]: [%s] to database.",
                tsetmc_identity.sector_code,
                tsetmc_identity.sector_title
            )
            session.add(IndustrySector(
                industry_sector_id=tsetmc_identity.sector_code,
                title=tsetmc_identity.sector_title
            ))
        current_sub_sector = session.query(IndustrySubSector).where(
            IndustrySubSector.industry_sub_sector_id == tsetmc_identity.sub_sector_code
        ).first()
        if not current_sub_sector:
            self._logger.info(
                "Adding sub sector [%d]: [%s] to database.",
                tsetmc_identity.sub_sector_code,
                tsetmc_identity.sub_sector_title
            )
            session.add(IndustrySubSector(
                industry_sector_id=tsetmc_identity.sector_code,
                title=tsetmc_identity.sub_sector_title,
                industry_sub_sector_id=tsetmc_identity.sub_sector_code
            ))

    async def __get_instrument_identity(
            self,
            instrument: InstrumentIdentification
    ):
        """Gets instrument data from TSETMC"""
        try:
            async with tsetmc.TsetmcScraper() as scraper:
                tsetmc_identity = await scraper.get_instrument_identity(
                    tsetmc_code=instrument.tsetmc_code,
                    timeout=10
                )
        except httpx.ConnectTimeout as exc:
            raise line.TaskException("Timeout on TSETMC request.") from exc
        return tsetmc_identity

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
