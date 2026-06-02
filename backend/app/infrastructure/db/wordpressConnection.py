
from app.infrastructure.db.config import settings
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from urllib.parse import quote_plus

WORDPRESS_DATABASE_URL = (
    f"mysql+pymysql://{settings.WP_DB_USER}:{quote_plus(settings.WP_DB_PASSWORD)}"
    f"@{settings.WP_DB_HOST}:{settings.WP_DB_PORT}/{settings.WP_DB_NAME}"
)

wordpressEngine = create_engine(
    WORDPRESS_DATABASE_URL,
    echo=settings.APP_DEBUG,
    pool_pre_ping=True
)

WordpressSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=wordpressEngine
)

def getWordpressDb():
    db = WordpressSessionLocal()
    try:
        yield db
    finally:
        db.close()