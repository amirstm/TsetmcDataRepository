"""
Using the line implementation in this module, \
one can fetch daily historical data for indices from TSETMC.
"""
import httpx
import sqlalchemy
from telegram_task import line
from tse_utils import tsetmc
from models.tse_market import (
    get_tse_market_session,
    IndexIdentification,
    DailyIndexValue,
)


class TsetmcIndexHistoricalCatcher(line.Worker):
    """Overriden worker for module tsetmc_index_historical_catcher"""

    async def perform_task(
        self, job_description: line.JobDescription
    ) -> line.JobReport:
        """Performs the task using the provided job description"""
        report = line.JobReport()
        indices, max_record_dates = self.__get_indices()
        report.information.append(
            f"Indices count ➡️ {len(indices)}",
        )
        await self.__update_historical_data(
            indices=indices, max_record_dates=max_record_dates, report=report
        )
        return report

    @classmethod
    def default_job_description(cls) -> line.JobDescription:
        """Creates the default job description for this worker"""
        return line.JobDescription()

    async def __update_historical_data(
        self,
        indices: list[IndexIdentification],
        max_record_dates: list[DailyIndexValue],
        report: line.JobReport,
    ) -> None:
        """Fetches Tsetmc data and adds new data to database"""
        success = 0
        failure = 0
        new_batch_data = []
        async with tsetmc.TsetmcScraper() as scraper:
            for index in indices:
                previous_last_record = next(
                    (x for x in max_record_dates if x.isin == index.isin), None
                )
                try:
                    self._LOGGER.info("Catching historical data for %s", repr(index))
                    index_data = await scraper.get_index_history(
                        tsetmc_code=index.tsetmc_code
                    )
                    success += 1
                except (httpx.RequestError, tsetmc.TsetmcScrapeException):
                    self._LOGGER.error(
                        "Catching historical data failed for %s", repr(index)
                    )
                    failure += 1
                    continue
                new_data = [
                    self.index_data_tsetmc_to_db(isin=index.isin, tsetmc_data=x)
                    for x in index_data
                    if (
                        previous_last_record is None
                        or x.record_date > previous_last_record.record_date
                    )
                ]
                new_batch_data.extend(new_data)
        if new_batch_data:
            self.insert_batch_in_database(new_batch_data)
        report.information.extend(
            [
                f"Historical data inserted ➡️ {len(new_batch_data)}",
                f"Index catch success ➡️ {success}",
                f"Index catch failure ➡️ {failure}",
            ]
        )

    def insert_batch_in_database(self, new_batch_data: list[DailyIndexValue]) -> int:
        """Inserts a batch of index data into database"""
        with get_tse_market_session() as session:
            session.add_all(new_batch_data)
            self._LOGGER.info(
                "Inserting %d DailyIndexValue rows into database.", len(new_batch_data)
            )
            row_num = len(new_batch_data)
            session.commit()
            return row_num

    @classmethod
    def index_data_tsetmc_to_db(
        cls, isin: str, tsetmc_data: tsetmc.IndexDaily
    ) -> DailyIndexValue:
        """Converts tsetmc index data to database model"""
        return DailyIndexValue(
            isin=isin,
            record_date=tsetmc_data.record_date,
            max_value=tsetmc_data.max_value,
            min_value=tsetmc_data.min_value,
            close_value=tsetmc_data.close_value,
        )

    def __get_indices(self) -> tuple[list[IndexIdentification], DailyIndexValue]:
        """Gets list of indices from database"""
        with get_tse_market_session() as session:
            indices = session.query(IndexIdentification).all()
            # pylint: disable=not-callable
            # sqlalchemy.func.max is indeed callable
            subq = (
                session.query(
                    DailyIndexValue.isin,
                    sqlalchemy.func.max(DailyIndexValue.record_date).label("maxdate"),
                )
                .group_by(DailyIndexValue.isin)
                .subquery("t2")
            )
            query = session.query(DailyIndexValue).join(
                subq,
                sqlalchemy.and_(
                    DailyIndexValue.isin == subq.c.isin,
                    DailyIndexValue.record_date == subq.c.maxdate,
                ),
            )
            max_record_dates = query.all()
            return indices, max_record_dates
