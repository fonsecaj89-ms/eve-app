from sqlmodel import create_engine, SQLModel, Session
from app.logger import structlog
import os

logger = structlog.get_logger()

POSTGRES_USER = os.getenv("POSTGRES_USER", "eve_admin")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "change_me_securely")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres") # 'postgres' is the docker service name
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "eve_db")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(DATABASE_URL, echo=False, future=True)

def create_db_and_tables():
    logger.info("db_initialization", status="starting")
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("db_initialization", status="success")
    except Exception as e:
        logger.error("db_initialization", status="failed", error=str(e))
        raise e

def get_session():
    with Session(engine) as session:
        yield session
