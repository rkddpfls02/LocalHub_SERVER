from app.db.database import SessionLocal, init_db
from app.utils.load_json_data import load_festival_json, load_place_jsons


if __name__ == "__main__":
    init_db()
    db = SessionLocal()
    try:
        place_count = load_place_jsons(db, overwrite=True)
        festival_count = load_festival_json(db, overwrite=True)
        print(f"Imported {place_count} places")
        print(f"Imported {festival_count} festivals")
    finally:
        db.close()
