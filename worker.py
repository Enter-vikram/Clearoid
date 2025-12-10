from rq import Worker, Queue
from redis import Redis

redis_conn = Redis()

listen = ['default']

if __name__ == '__main__':
    queues = [Queue(name, connection=redis_conn) for name in listen]
    worker = Worker(queues, connection=redis_conn)
    worker.work()
