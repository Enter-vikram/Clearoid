# worker.py
from rq import Worker, Queue
from redis import Redis

redis_conn = Redis(host='localhost', port=6379, db=0)

if __name__ == '__main__':
    queues = [Queue('default', connection=redis_conn)]
    worker = Worker(queues, connection=redis_conn)
    worker.work()