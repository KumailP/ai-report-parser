from typing import Annotated
from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine, select
from app.logger import logger
from app.models import PositionType
from app.constants import STANDARD_POSITIONS_TO_INITIALIZE

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def init_position_types(session: Session):
    existing = session.exec(select(PositionType).limit(1)).first()
    if existing:
        logger.info("Position types already initialized")
        return

    logger.info("Initializing position types")
    for category, positions in STANDARD_POSITIONS_TO_INITIALIZE.items():
        for code, description in positions:
            position_type = PositionType(
                code=code,
                description=description,
                category=category
            )
            session.add(position_type)
    
    session.commit()
    logger.info(f"Added {sum(len(positions) for positions in STANDARD_POSITIONS_TO_INITIALIZE.values())} position types")

def create_db_and_tables():
    logger.info("Creating database and tables")
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        init_position_types(session)
    
    logger.info("Database initialization complete")

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]