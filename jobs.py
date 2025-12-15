# jobs.py
from redis import Redis
from rq import Queue
import os
import pandas as pd
from services.title_service import process_bulk_titles
from database.database import get_db
from sqlalchemy.orm import Session

redis_conn = Redis(host='localhost', port=6379, db=0)
q = Queue(connection=redis_conn)

def process_file_bulk(temp_path: str):
    db: Session = next(get_db())
    try:
        df = pd.read_excel(temp_path)
        result = process_bulk_titles(db, df)
        print(f"Bulk processing complete: {result}")
        # Optional: delete temp file
        os.remove(temp_path)
        return result
    except Exception as e:
        print(f"Error in bulk processing: {e}")
        return {"error": str(e)}
    finally:
        db.close()