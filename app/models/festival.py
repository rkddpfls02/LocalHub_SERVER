from sqlalchemy import Column, Date, Integer, String, UniqueConstraint

from app.db.database import Base


class Festival(Base):
    __tablename__ = "festivals"
    __table_args__ = (
        UniqueConstraint("title", "start_date", "end_date", name="uq_festival_schedule"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    addr1 = Column(String(500), nullable=False, default="")
