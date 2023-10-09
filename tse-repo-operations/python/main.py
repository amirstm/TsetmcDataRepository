"""Starting point for the execution of the project"""
import os
import logging
import asyncio
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from dotenv import load_dotenv
import telegram.ext
from telegram_task.president import President, TelegramDeputy
from telegram_task.line import (
    LineManager,
    CronJobOrder,
)
from lines.tse_client_instruments_updater import TseClientInstrumentsUpdater

load_dotenv()

PROXY_URL = os.getenv('PROXY_URL')
PROXY_URL = PROXY_URL if PROXY_URL else None
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MYSQL_DB = os.getenv("MYSQL_DB")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")


async def main():
    """Manually testing the enterprise"""
    logger = logging.getLogger("telegram_task")
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s: %(message)s'
    )
    logger.setLevel(logging.INFO)
    log_file_path = "logs/log_"
    file_handler = TimedRotatingFileHandler(
        filename=log_file_path,
        when='midnight',
        backupCount=30
    )
    file_handler.suffix = '%Y_%m_%d.log'
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    application = telegram.ext.ApplicationBuilder().proxy_url(
        PROXY_URL
    ).token(
        TELEGRAM_BOT_TOKEN
    ).build()
    president = President(
        telegram_deputy=TelegramDeputy(
            telegram_app=application,
            telegram_admin_id=TELEGRAM_CHAT_ID
        )
    )
    president.add_line(
        LineManager(
            worker=TseClientInstrumentsUpdater(),
            cron_job_orders=[
                CronJobOrder(
                    daily_run_time=(
                        datetime.now() + timedelta(seconds=3)
                    ).time(),
                    job_description=TseClientInstrumentsUpdater.default_job_description()
                )
            ]
        )
    )
    await president.start_operation_async()


if __name__ == '__main__':
    asyncio.new_event_loop().run_until_complete(main())
