from app.db.database import SessionLocal, init_db
from app.utils.load_json_data import load_place_jsons


if __name__ == "__main__":
    init_db()
    db = SessionLocal()
    try:
        count = load_place_jsons(db, overwrite=True)
        print(f"Imported {count} places")
    finally:
        db.close()
