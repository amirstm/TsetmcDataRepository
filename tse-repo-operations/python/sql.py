from sqlalchemy import ForeignKey
from typing import List
from sqlalchemy.orm import relationship
from typing import Optional
from sqlalchemy import String
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import mapper, sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

PROXY_URL = os.getenv('PROXY_URL')
PROXY_URL = PROXY_URL if PROXY_URL else None
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_DB = os.getenv("MYSQL_DB")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PORT = os.getenv("MYSQL_PORT")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")


Base = declarative_base()

mysql_connector = "mysql+mysqlconnector://{}:{}@{}:{}/{}".format(
    MYSQL_USER,
    MYSQL_PASSWORD,
    MYSQL_HOST,
    MYSQL_PORT,
    MYSQL_DB
)
print(mysql_connector)
engine = create_engine(
    mysql_connector,
    echo=True
)


class InstrumentType(Base):
    __tablename__ = "InstrumentType"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(32))

    # instrument_identifications: Mapped[List["InstrumentIdentification"]] = relationship(
    #     back_populates="InstrumentType", cascade="all, delete-orphan"
    # )

    def __repr__(self) -> str:
        return f"InstrumentType(id={self.id!r}, title={self.title!r})"


class InstrumentIdentification(Base):
    __tablename__ = "InstrumentIdentification"

    isin: Mapped[str] = mapped_column(String(length=12), primary_key=True)
    tsetmc_code: Mapped[str] = mapped_column(String(32), name="TsetmcCode")
    ticker: Mapped[str] = mapped_column(String(32))

    # instrument_type_id: Mapped[int] = mapped_column(
    #     ForeignKey("InstrumentType.id"))

    # InstrumentType: Mapped["InstrumentType"] = relationship(
    #     back_populates="InstrumentIdentification")

    def __repr__(self) -> str:
        return f"InstrumentIdentification(isin={self.isin!r})"


def loadSession():
    """"""

    Session = sessionmaker(bind=engine)
    session = Session()
    return session


if __name__ == "__main__":
    session = loadSession()
    res = session.query(InstrumentType).all()
    print(res[0])
    res = session.query(InstrumentIdentification).all()
    print(res[0])
