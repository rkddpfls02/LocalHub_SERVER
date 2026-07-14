from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.db.database import Base


class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(String(50), unique=True, index=True, nullable=False)
    region = Column(String(50), nullable=False)
    content_type = Column(String(50), nullable=False)
    content_type_id = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    addr1 = Column(String(500))
    addr2 = Column(String(500))
    areacode = Column(String(50))
    cat1 = Column(String(50))
    cat2 = Column(String(50))
    cat3 = Column(String(50))
    tel = Column(String(100))
    zipcode = Column(String(20))
    first_image = Column(String(1000))
    first_image2 = Column(String(1000))
    cpyrht_div_cd = Column(String(50))
    mapx = Column(String(50))
    mapy = Column(String(50))
    mlevel = Column(String(20))
    sigungucode = Column(String(20))
    l_dong_regn_cd = Column(String(20))
    l_dong_signgu_cd = Column(String(20))
    lcls_systm1 = Column(String(50))
    lcls_systm2 = Column(String(50))
    lcls_systm3 = Column(String(50))
    created_time = Column(String(14))
    modified_time = Column(String(14))
    raw_data = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
