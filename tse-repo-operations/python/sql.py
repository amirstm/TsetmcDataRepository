from __future__ import annotations
import os
from datetime import date, datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.tse_market import InstrumentType, get_tse_market_session


if __name__ == "__main__":
    # res = session.query(InstrumentType).all()
    # print(res[0])
    # res = session.query(InstrumentIdentification).all()
    # print(res[0])
    # with sessionmaker(bind=engine)() as session:
    with get_tse_market_session() as session:
        res = session.query(InstrumentType).where(
            InstrumentType.instrument_type_id == 12345
        ).first()
        print(res.instrument_identifications)
