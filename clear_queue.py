from redis import Redis
from rq import Queue

redis_conn = Redis(host="localhost", port=6379)
q = Queue("video_queue", connection=redis_conn)

q.empty()
print("Queue cleared successfully!")