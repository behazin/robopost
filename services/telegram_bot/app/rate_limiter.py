import asyncio
import time
import logging
from collections import deque

logger = logging.getLogger(__name__)

class MessageRateLimiter:
    """
    A simple asyncio-compatible rate limiter.
    It ensures that the number of actions does not exceed the rate limit
    within a given time window using a sliding window of timestamps.
    """
    def __init__(self, rate_limit: int, per_seconds: int):
        self.rate_limit = rate_limit
        self.per_seconds = per_seconds
        self.timestamps = deque()
        logger.info(f"Rate limiter initialized: {rate_limit} requests per {per_seconds} seconds.")

    async def wait(self):
        """Waits if necessary to respect the rate limit before proceeding."""
        while True:
            now = time.monotonic()
            while self.timestamps and self.timestamps[0] <= now - self.per_seconds:
                self.timestamps.popleft()

            if len(self.timestamps) < self.rate_limit:
                self.timestamps.append(now)
                break
            
            time_to_wait = self.timestamps[0] + self.per_seconds - now
            await asyncio.sleep(time_to_wait)