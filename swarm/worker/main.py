#!/usr/bin/env python3
"""Worker service that polls Redis for jobs and routes to Bridge API."""

import hashlib
import hmac
import json
import logging
import time
from typing import Optional

import redis
import requests
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class JobWorker:
    """Worker that polls Redis for jobs and executes them via Bridge API."""

    def __init__(self):
        self.config = Config()
        self.redis_client: Optional[redis.Redis] = None
        self.running = False

    def connect_redis(self) -> bool:
        """Connect to Redis. Returns True on success."""
        try:
            self.redis_client = redis.Redis(
                host=self.config.REDIS_HOST,
                port=self.config.REDIS_PORT,
                db=self.config.REDIS_DB,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.config.REDIS_HOST}:{self.config.REDIS_PORT}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return False

    def sign_request(self, payload: dict) -> str:
        """Sign request payload with HMAC-SHA256."""
        body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        signature = hmac.new(
            self.config.HMAC_SECRET.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature

    def poll_job(self) -> Optional[dict]:
        """Poll Redis for next job. Returns job dict or None."""
        if not self.redis_client:
            return None

        try:
            # Use BLPOP for blocking pop with timeout
            result = self.redis_client.blpop("swarm:jobs:pending", timeout=1)
            if result:
                _, job_json = result
                job = json.loads(job_json)
                logger.info(f"Dequeued job: {job.get('job_id')}")
                return job
            return None
        except Exception as e:
            logger.error(f"Error polling job: {e}")
            return None

    def execute_job(self, job: dict) -> dict:
        """Execute job via Bridge API. Returns result dict."""
        job_id = job.get("job_id")
        capability = job.get("capability")
        parameters = job.get("parameters", {})

        logger.info(f"Executing job {job_id}: {capability}")

        # Sign the request
        payload = {
            "job_id": job_id,
            "capability": capability,
            "parameters": parameters
        }
        signature = self.sign_request(payload)

        try:
            response = requests.post(
                f"{self.config.BRIDGE_BASE_URL}/execute",
                json=payload,
                headers={"X-Swarm-Signature": signature},
                timeout=300
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Job {job_id} completed successfully")
            return {
                "status": "success",
                "result": result,
                "completed_at": time.time()
            }
        except requests.exceptions.Timeout:
            logger.error(f"Job {job_id} timed out")
            return {
                "status": "timeout",
                "error": "Request to bridge timed out",
                "completed_at": time.time()
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Job {job_id} failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "completed_at": time.time()
            }

    def store_result(self, job_id: str, result: dict):
        """Store job result in Redis."""
        if not self.redis_client:
            return

        try:
            key = f"swarm:jobs:result:{job_id}"
            self.redis_client.setex(
                key,
                86400,  # 24 hour TTL
                json.dumps(result)
            )
            logger.info(f"Stored result for job {job_id}")
        except Exception as e:
            logger.error(f"Failed to store result: {e}")

    def run(self):
        """Main worker loop."""
        logger.info("Starting AI Swarm Worker")

        # Validate config
        try:
            self.config.validate()
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            raise

        # Connect to Redis
        if not self.connect_redis():
            raise RuntimeError("Failed to connect to Redis")

        self.running = True
        logger.info(f"Worker ready. Polling every {self.config.POLL_INTERVAL}s")

        while self.running:
            try:
                job = self.poll_job()
                if job:
                    result = self.execute_job(job)
                    self.store_result(job.get("job_id"), result)
                else:
                    time.sleep(self.config.POLL_INTERVAL)
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                self.running = False
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(self.config.POLL_INTERVAL)

        logger.info("Worker stopped")


def main():
    """Entry point."""
    worker = JobWorker()
    worker.run()


if __name__ == "__main__":
    main()
