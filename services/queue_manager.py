import asyncio
from typing import Dict, Any, Callable, Awaitable
from logger import get_logger

logger = get_logger(__name__)

class QueueManager:
    """
    Manages a strict FIFO queue of downloads.
    Only allows 1 concurrent download to save RAM.
    """
    def __init__(self):
        self.queue = asyncio.Queue()
        self.active_task: Dict[str, Any] = {}
        self.queue_list = []  # To keep track of positions
        self._worker_task = None

    async def add_job(self, user_id: int, job_data: dict, callback: Callable[[dict], Awaitable[None]]):
        """
        Add a download job to the queue.
        `job_data` contains url, format_id, message references.
        `callback` is the async function to execute when it's the job's turn.
        """
        job = {
            "user_id": user_id,
            "data": job_data,
            "callback": callback
        }
        await self.queue.put(job)
        self.queue_list.append(job)
        logger.info(f"Job added to queue for user {user_id}. Queue size: {len(self.queue_list)}")
        return len(self.queue_list)

    def get_position(self, user_id: int) -> int:
        """Get the queue position for a user. Returns 0 if active, -1 if not found."""
        if self.active_task and self.active_task.get("user_id") == user_id:
            return 0
            
        for i, job in enumerate(self.queue_list):
            if job["user_id"] == user_id:
                return i + 1
        return -1

    def cancel_job(self, user_id: int) -> bool:
        """
        Cancel a job for a user in the queue. 
        Cannot easily cancel the active task cleanly here without subprocess management, 
        so we focus on removing from pending queue.
        """
        for i, job in enumerate(self.queue_list):
            if job["user_id"] == user_id:
                self.queue_list.pop(i)
                # Rebuild queue (asyncio.Queue has no remove method)
                new_queue = asyncio.Queue()
                for j in self.queue_list:
                    new_queue.put_nowait(j)
                self.queue = new_queue
                logger.info(f"Cancelled queued job for user {user_id}")
                return True
        return False

    def get_queue_stats(self) -> dict:
        return {
            "active": self.active_task.get("user_id") if self.active_task else None,
            "pending_count": len(self.queue_list)
        }

    async def worker(self):
        """Background worker to process the queue."""
        logger.info("Queue worker started")
        while True:
            job = await self.queue.get()
            # Remove from tracking list
            if job in self.queue_list:
                self.queue_list.remove(job)
                
            self.active_task = job
            user_id = job["user_id"]
            
            logger.info(f"Starting job for user {user_id}")
            try:
                await job["callback"](job["data"])
            except Exception as e:
                logger.error(f"Error processing job for user {user_id}: {e}")
            finally:
                self.active_task = {}
                self.queue.task_done()
                logger.info(f"Finished job for user {user_id}")

    def start(self):
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self.worker())
            
queue_manager = QueueManager()
