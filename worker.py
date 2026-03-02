from redis import Redis
from rq import Connection
from rq.worker import SimpleWorker
from rq.timeouts import BaseDeathPenalty

# 👇 Custom death penalty that does nothing (Windows safe)
class NoDeathPenalty(BaseDeathPenalty):
    def handle_death_penalty(self, *args, **kwargs):
        pass

    def setup_death_penalty(self):
        pass

    def cancel_death_penalty(self):
        pass


redis_conn = Redis(host="localhost", port=6379)

if __name__ == "__main__":
    with Connection(redis_conn):
        worker = SimpleWorker(
            ["video_queue"],
            connection=redis_conn
        )

        # 👇 Disable timeout system completely
        worker.death_penalty_class = NoDeathPenalty

        worker.work()