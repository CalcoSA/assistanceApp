from sqlalchemy.orm import sessionmaker, declarative_base
from app.infrastructure.db.config import settings
from sqlalchemy import create_engine
from urllib.parse import quote_plus

DATABASE_URL = (
    f"mysql+pymysql://{settings.DB_USER}:{quote_plus(settings.DB_PASSWORD)}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    echo=settings.APP_DEBUG,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def getDb():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()