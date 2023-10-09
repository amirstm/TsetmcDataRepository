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


@dataclass
class JobDescription(line.JobDescription):
    """Overriden JobDescription for module tse_client_instruments_updater"""
    min_acceptable_last_change_date: date = None


class TseClientInstrumentsUpdater(line.Worker):
    """Overriden worker for module tse_client_instruments_updater"""

    async def perform_task(self, job_description: JobDescription) -> line.JobReport:
        """Performs the task using the provided job description"""
        instruments, indices = await self.__get_global_instruments_from_tse_client(
            job_description=job_description
        )
        self.__update_database(instruments, indices)
        return line.JobReport(
            information=[
                f"Result ➡️ {job_description.min_acceptable_last_change_date}"
            ]
        )

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
            indices: list[TseClientInstrumentIdentitification]
    ):
        """Updates the database with the instruments and the indices"""

    async def __get_global_instruments_from_tse_client(
            self, job_description: JobDescription
    ) -> tuple[
        list[TseClientInstrumentIdentitification],
        list[TseClientInstrumentIdentitification]
    ]:
        """Get instruments from TSE client"""
        self._LOGGER.info("Fetching global instruments.")
        async with TseClientScraper() as tse_client:
            instruments, indices = await tse_client.get_instruments_list()
        self._LOGGER.info(
            "Total instruments count: [%d], Total indices count: [%d]",
            len(instruments),
            len(indices)
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
