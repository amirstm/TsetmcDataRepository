"""
Using the line implementation in this module, \
the instruments table in the database will be kept up-to-date.
"""
from dataclasses import dataclass
from datetime import date
from telegram_task import line


@dataclass
class JobDescription(line.JobDescription):
    """Overriden JobDescription for module tse_client_instruments_updater"""
    min_acceptable_last_change_date: date = None


class TseClientInstrumentsUpdater(line.Worker):
    """Overriden worker for module tse_client_instruments_updater"""

    async def perform_task(self, job_description: JobDescription) -> line.JobReport:
        """Performs the task using the provided job description"""
        return line.JobReport(
            information=[
                f"Result ➡️ {job_description.min_acceptable_last_change_date}"
            ]
        )

    @classmethod
    def default_job_description(cls) -> JobDescription:
        """Creates the default job description for this worker"""
        return JobDescription(
            min_acceptable_last_change_date=date(year=2023, month=1, day=1)
        )
