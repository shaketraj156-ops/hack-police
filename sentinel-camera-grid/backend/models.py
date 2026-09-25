from sqlalchemy import Column, Integer, String, DateTime
from database import Base

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(String, unique=True, index=True) # cam01 to cam30
    display_name = Column(String)                         # CAM-01
    location = Column(String)                             # City name or coordinates
    hls_url = Column(String)
    status = Column(String, default="ONLINE")             # ONLINE or OFFLINE
    last_seen = Column(DateTime(timezone=True), nullable=True)

class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String, unique=True, index=True) # e.g., GJ01AB1234
    vehicle_type = Column(String)