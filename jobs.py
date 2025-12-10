from rq import Queue
from redis import Redis

redis_conn = Redis()  # connects to localhost:6379
q = Queue(connection=redis_conn)

def process_file(file_id):
    # placeholder job logic
    print(f"Processing file {file_id}")
    return {"file_id": file_id, "status": "done"}
