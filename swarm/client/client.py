#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Client for enqueuing jobs to the AI Swarm."""

import json
import logging
import time
import uuid
from typing import Optional

import redis
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class JobQueue:
    """Client for enqueuing jobs to the AI Swarm."""

    REDIS_QUEUE = "swarm:jobs:pending"
    REDIS_RESULT_PREFIX = "swarm:jobs:result:"
    RESULT_TTL = 86400  # 24 hours

    def __init__(self):
        self.config = Config()
        self.redis_client: Optional[redis.Redis] = None

    def connect(self) -> bool:
        """Connect to Redis. Returns True on success."""
        try:
            self.redis_client = redis.Redis(
                host=self.config.REDIS_HOST,
                port=self.config.REDIS_PORT,
                db=self.config.REDIS_DB,
                decode_responses=True,
            )
            self.redis_client.ping()
            logger.info(
                f"Connected to Redis at {self.config.REDIS_HOST}:{self.config.REDIS_PORT}",
            )
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return False

    def enqueue(
        self,
        capability: str,
        parameters: dict,
        job_id: Optional[str] = None,
    ) -> str:
        """Enqueue a job to the swarm.

        Args:
            capability: The capability to execute (e.g., "browser:open")
            parameters: Parameters for the capability
            job_id: Optional job ID (generated if not provided)

        Returns:
            The job ID
        """
        if not self.redis_client:
            raise RuntimeError("Not connected to Redis")

        job_id = job_id or str(uuid.uuid4())
        job = {
            "job_id": job_id,
            "capability": capability,
            "parameters": parameters,
            "enqueued_at": time.time(),
        }

        try:
            self.redis_client.lpush(self.REDIS_QUEUE, json.dumps(job))
            logger.info(f"Enqueued job {job_id}: {capability}")
            return job_id
        except Exception as e:
            logger.error(f"Failed to enqueue job: {e}")
            raise

    def get_result(self, job_id: str, timeout: float = 0) -> Optional[dict]:
        """Get the result of a job.

        Args:
            job_id: The job ID to get result for
            timeout: Seconds to wait for result (0 = immediate)

        Returns:
            Job result dict or None if not ready
        """
        if not self.redis_client:
            raise RuntimeError("Not connected to Redis")

        import time

        key = f"{self.REDIS_RESULT_PREFIX}{job_id}"
        start = time.time()

        while True:
            result = self.redis_client.get(key)
            if result:
                logger.info(f"Got result for job {job_id}")
                return json.loads(result)

            if timeout == 0:
                return None

            if time.time() - start >= timeout:
                return None

            time.sleep(0.5)

    def execute(
        self,
        capability: str,
        parameters: dict,
        timeout: float = 300.0,
    ) -> dict:
        """Enqueue a job and wait for the result.

        Args:
            capability: The capability to execute
            parameters: Parameters for the capability
            timeout: Maximum seconds to wait for result

        Returns:
            Job result dict

        Raises:
            TimeoutError: If result not received within timeout
        """
        import time

        job_id = self.enqueue(capability, parameters)
        result = self.get_result(job_id, timeout)

        if result is None:
            raise TimeoutError(f"Job {job_id} timed out")

        return result


# Convenience functions for common use
def enqueue_job(capability: str, **kwargs) -> str:
    """Enqueue a job with the given capability and parameters."""
    queue = JobQueue()
    if not queue.connect():
        raise RuntimeError("Failed to connect to Redis")
    return queue.enqueue(capability, kwargs)


def execute_job(capability: str, timeout: float = 300.0, **kwargs) -> dict:
    """Execute a job and wait for the result."""
    queue = JobQueue()
    if not queue.connect():
        raise RuntimeError("Failed to connect to Redis")
    return queue.execute(capability, kwargs, timeout)


if __name__ == "__main__":
    import sys
    import time

    if len(sys.argv) < 2:
        print("Usage: python client.py <capability> [param1=value1] ...")
        sys.exit(1)

    capability = sys.argv[1]
    parameters = {}

    for arg in sys.argv[2:]:
        if "=" in arg:
            key, value = arg.split("=", 1)
            parameters[key] = value

    queue = JobQueue()
    if not queue.connect():
        print("Failed to connect to Redis")
        sys.exit(1)

    job_id = queue.enqueue(capability, parameters)
    print(f"Enqueued job: {job_id}")

    print("Waiting for result...")
    try:
        result = queue.get_result(job_id, timeout=60)
        print(json.dumps(result, indent=2))
    except TimeoutError:
        print("Timeout waiting for result")
