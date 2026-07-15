from sqlalchemy import Column, Date, Integer, String, Text, UniqueConstraint

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
    content_id = Column(String(50), nullable=True, index=True)
    first_image = Column(String(1000), nullable=True)
    first_image2 = Column(String(1000), nullable=True)
    eventstartdate = Column(String(8), nullable=True)
    eventenddate = Column(String(8), nullable=True)
    eventplace = Column(String(500), nullable=True)
    playtime = Column(String(255), nullable=True)
    program = Column(Text, nullable=True)
    subevent = Column(Text, nullable=True)
    sponsor1 = Column(String(500), nullable=True)
    sponsor1tel = Column(String(255), nullable=True)
    sponsor2 = Column(String(500), nullable=True)
    sponsor2tel = Column(String(255), nullable=True)
    eventhomepage = Column(String(500), nullable=True)
    bookingplace = Column(String(500), nullable=True)
    agelimit = Column(String(255), nullable=True)
    festivalgrade = Column(String(255), nullable=True)
    placeinfo = Column(Text, nullable=True)
    spendtimefestival = Column(String(255), nullable=True)
    discountinfofestival = Column(String(255), nullable=True)
    usetimefestival = Column(Text, nullable=True)
