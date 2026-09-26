from database import engine, Base, SessionLocal
from models import Camera, Watchlist
from sqlalchemy import text
import datetime

def init_db():
    # Construct tables based on models.py
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Optional: Enable PostGIS for future map coordination
    try:
        db.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        db.commit()
    except Exception:
        print("Note: PostGIS extension not installed locally. Continuing standard setup.")
        db.rollback()
        

    # Seed the 30 mock cameras to replace the frontend's hardcoded catalog
    if db.query(Camera).count() == 0:
        print("Seeding 30 cameras...")
        for i in range(1, 31):
            cam_num = str(i).zfill(2)
            db.add(Camera(
                provider_id=f"cam{cam_num}",
                display_name=f"CAM-{cam_num}",
                location="Ahmedabad",
                hls_url=f"https://cctv.corp8.cloud/cam{cam_num}/index.m3u8",
                status="OFFLINE" if i == 3 else "ONLINE",
                last_seen=datetime.datetime.utcnow()
            ))
        
        # Seed the synthetic watchlist for the ANPR models to match against
        dummy_plates = ["GJ01AB1234", "MH14XY9999", "DL01ZZ0000"]
        for plate in dummy_plates:
            db.add(Watchlist(plate_number=plate, vehicle_type="SUV"))
            
        db.commit()
        print("Phase 2 Complete: Database seeded successfully!")
    else:
        print("Database already contains data. Skipping seed.")
        
    db.close()

if __name__ == "__main__":
    init_db()