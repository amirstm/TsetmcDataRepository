"""Starting point for the execution of the project"""
import os
import logging
from datetime import datetime, time, timedelta
from logging.handlers import TimedRotatingFileHandler
from dotenv import load_dotenv
import telegram.ext
from telegram_task.president import President, TelegramDeputy
from telegram_task.line import (
    LineManager,
    CronJobOrder,
)
from telegram_task.samples import (
    SleepyWorker,
    CalculatorJobDescription,
    CalculatorWorker,
    MathematicalOperation
)

load_dotenv()

PROXY_URL = os.getenv('PROXY_URL')
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def main():
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
    line_manager_1 = LineManager(
        worker=SleepyWorker(),
        cron_job_orders=[
            CronJobOrder((datetime.now() + timedelta(seconds=600)).time())
        ]
    )
    line_manager_2 = LineManager(
        worker=CalculatorWorker(),
        cron_job_orders=[
            CronJobOrder(
                daily_run_time=(
                    datetime.now() + timedelta(seconds=1200)
                ).time(),
                job_description=CalculatorJobDescription(
                    input1=2,
                    input2=3,
                    operation=MathematicalOperation.POW
                )
            ),
            CronJobOrder(
                daily_run_time=time(hour=23, minute=59, second=57),
                job_description=CalculatorJobDescription(
                    input1=2,
                    input2=3,
                    operation=MathematicalOperation.MUL
                )
            )]
    )
    president.add_line(line_manager_1, line_manager_2)
    president.start_operation()


if __name__ == '__main__':
    main()
