from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./tourism.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:
    """Enable SQLite FK constraints, including ON DELETE CASCADE."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db() -> None:
    from app.models import Festival, Place, Post, PostImage

    Base.metadata.create_all(bind=engine)
    _migrate_empty_legacy_post_tables()
    _ensure_festival_columns()


def _ensure_festival_columns() -> None:
    inspector = inspect(engine)
    if "festivals" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("festivals")}
    required_columns = {
        "eventstartdate": "TEXT",
        "eventenddate": "TEXT",
        "content_id": "TEXT",
        "first_image": "TEXT",
        "first_image2": "TEXT",
        "eventplace": "TEXT",
        "playtime": "TEXT",
        "program": "TEXT",
        "subevent": "TEXT",
        "sponsor1": "TEXT",
        "sponsor1tel": "TEXT",
        "sponsor2": "TEXT",
        "sponsor2tel": "TEXT",
        "eventhomepage": "TEXT",
        "bookingplace": "TEXT",
        "agelimit": "TEXT",
        "festivalgrade": "TEXT",
        "placeinfo": "TEXT",
        "spendtimefestival": "TEXT",
        "discountinfofestival": "TEXT",
        "usetimefestival": "TEXT",
    }

    with engine.begin() as connection:
        for column_name, column_type in required_columns.items():
            if column_name in existing_columns:
                continue
            connection.execute(text(f"ALTER TABLE festivals ADD COLUMN {column_name} {column_type}"))

    _backfill_festival_images()
    _ensure_place_review_columns()


def _backfill_festival_images() -> None:
    from app.utils.load_json_data import backfill_festival_images

    db = SessionLocal()
    try:
        backfill_festival_images(db)
    finally:
        db.close()


def _ensure_place_review_columns() -> None:
    inspector = inspect(engine)
    if "places" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("places")}
    with engine.begin() as connection:
        if "avg_rating" not in existing_columns:
            connection.execute(text("ALTER TABLE places ADD COLUMN avg_rating REAL NOT NULL DEFAULT 0.0"))
        if "post_cnt" not in existing_columns:
            connection.execute(text("ALTER TABLE places ADD COLUMN post_cnt INTEGER NOT NULL DEFAULT 0"))


def _migrate_empty_legacy_post_tables() -> None:
    """Replace only empty tables created by the old file-path post implementation."""
    inspector = inspect(engine)
    if "posts" not in inspector.get_table_names():
        return

    post_columns = {column["name"] for column in inspector.get_columns("posts")}
    if "rating" not in post_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE posts ADD COLUMN rating INTEGER NOT NULL DEFAULT 5"))

    image_columns = (
        {column["name"] for column in inspector.get_columns("post_images")}
        if "post_images" in inspector.get_table_names()
        else set()
    )
    required_post_columns = {"place_id", "nickname", "password", "title", "content"}
    required_image_columns = {"post_id", "file_name", "content_type", "image_data"}
    if required_post_columns.issubset(post_columns) and required_image_columns.issubset(image_columns):
        return

    with engine.begin() as connection:
        post_count = connection.execute(text("SELECT COUNT(*) FROM posts")).scalar_one()
        image_count = (
            connection.execute(text("SELECT COUNT(*) FROM post_images")).scalar_one()
            if "post_images" in inspector.get_table_names()
            else 0
        )
        if post_count or image_count:
            raise RuntimeError(
                "기존 posts/post_images 테이블에 데이터가 있어 자동 스키마 변경을 중단했습니다. "
                "데이터 마이그레이션이 필요합니다."
            )
        if "post_images" in inspector.get_table_names():
            connection.execute(text("DROP TABLE post_images"))
        connection.execute(text("DROP TABLE posts"))

    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
