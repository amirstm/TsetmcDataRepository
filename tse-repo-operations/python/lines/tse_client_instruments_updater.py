"""
Using the line implementation in this module, \
the instruments table in the database will be kept up-to-date.
"""
from typing import Callable
from dataclasses import dataclass
from datetime import date
from telegram_task import line
from tse_utils.tse_client import (
    TseClientInstrumentIdentitification,
    TseClientScraper
)
from utils.persian_arabic import arabic_to_persian
from models.tse_market import (
    get_tse_market_session,
    InstrumentType,
    InstrumentIdentification
)


@dataclass
class JobDescription(line.JobDescription):
    """Overriden JobDescription for module tse_client_instruments_updater"""
    min_acceptable_last_change_date: date = None


class TseClientInstrumentsUpdater(line.Worker):
    """Overriden worker for module tse_client_instruments_updater"""

    async def perform_task(self, job_description: JobDescription) -> line.JobReport:
        """Performs the task using the provided job description"""
        report = line.JobReport(
            information=[
                f"Result ➡️ {job_description.min_acceptable_last_change_date}"
            ]
        )
        instruments, indices = await self.__get_global_instruments_from_tse_client(
            job_description=job_description,
            report=report
        )
        await self.__update_database(
            instruments=instruments,
            indices=indices,
            report=report
        )
        return report

    @classmethod
    def default_job_description(cls) -> JobDescription:
        """Creates the default job description for this worker"""
        return JobDescription(
            min_acceptable_last_change_date=date(
                year=2023,
                month=1,
                day=1
            )
        )

    async def __update_database(
            self,
            instruments: list[TseClientInstrumentIdentitification],
            indices: list[TseClientInstrumentIdentitification],
            report: line.JobReport
    ):
        """Updates the database with the instruments and the indices"""
        with get_tse_market_session() as session:
            instrument_types = session.query(InstrumentType).all()
            instruments_known_type = self.__filter_identifications_by_type(
                instruments,
                instrument_types,
                report
            )
            old_instruments = session.query(InstrumentIdentification).all()
            new_instruments = [
                x
                for x in instruments_known_type
                if not any(
                    y
                    for y in old_instruments
                    if y.isin == x.isin
                )
            ]
            session.add_all([
                self.tse_client_to_database_instrument_identification(
                    raw=x
                )
                for x in new_instruments
            ])
            session.commit()

    @classmethod
    def tse_client_to_database_instrument_identification(
        cls,
        raw: TseClientInstrumentIdentitification
    ) -> InstrumentIdentification:
        """Converts an instrument identification from TseClient to database model"""
        return InstrumentIdentification(
            isin=raw.isin,
            ticker=raw.ticker,
            tsetmc_code=raw.tsetmc_code,
            name_persian=raw.name_persian,
            name_english=raw.name_english,
            instrument_type_id=raw.type_id
        )

    def __filter_identifications_by_type(
            self,
            instruments: list[TseClientInstrumentIdentitification],
            instrument_types: list[InstrumentType],
            report: line.JobReport
    ) -> list[TseClientInstrumentIdentitification]:
        """Filters out the instruments with unknown types"""
        type_ids = [x.instrument_type_id for x in instrument_types]
        unknown = [
            x
            for x in instruments
            if x.type_id not in type_ids
        ]
        if unknown:
            report.information.append(
                f"Unknown types ➡️ {list(set([x.type_id for x in unknown]))!r}"
            )
            report.warnings.append(unknown.__repr__())
        known = [
            x
            for x in instruments
            if x.type_id in type_ids
        ]
        return known

    async def __get_global_instruments_from_tse_client(
            self,
            job_description: JobDescription,
            report: line.JobReport
    ) -> tuple[
        list[TseClientInstrumentIdentitification],
        list[TseClientInstrumentIdentitification]
    ]:
        """Get instruments from TSE client"""
        self._LOGGER.info("Fetching global instruments.")
        async with TseClientScraper() as tse_client:
            instruments, indices = await tse_client.get_instruments_list()
        self._LOGGER.info(
            "Global instruments count: [%d], Global indices count: [%d]",
            len(instruments),
            len(indices)
        )
        report.information.append(
            f"Global instruments ➡️ {len(instruments)}"
        )
        self.__pre_process_identifications(instruments)
        self.__pre_process_identifications(indices)
        instruments_ok, _ = self.__filter_by_last_change_date(
            identifications=instruments,
            job_description=job_description
        )
        self._LOGGER.info(
            "Filtered instruments count: [%d]",
            len(instruments_ok),
        )
        return instruments_ok, indices

    @classmethod
    def __pre_process_identifications(
        cls,
        identifications: list[TseClientInstrumentIdentitification],
    ) -> None:
        """Does necessary preprocessings on the identifications"""
        for identification in identifications:
            identification.ticker = arabic_to_persian(
                identification.ticker
            )
            identification.name_persian = arabic_to_persian(
                identification.name_persian
            )

    @classmethod
    def __filter_by_last_change_date(
        cls,
        identifications: list[TseClientInstrumentIdentitification],
        job_description: JobDescription
    ) -> tuple[
        list[TseClientInstrumentIdentitification],
        list[TseClientInstrumentIdentitification]
    ]:
        """Filter instruments list by last change date"""
        condition: Callable[
            [TseClientInstrumentIdentitification],
            bool
        ] = lambda x: x.last_change_date >= job_description.min_acceptable_last_change_date
        return [
            x
            for x in identifications
            if condition(x)
        ], [
            x
            for x in identifications
            if not condition(x)
        ]
