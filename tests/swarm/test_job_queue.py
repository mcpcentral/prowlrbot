# -*- coding: utf-8 -*-
"""Tests for job queue client."""

import json
import os
import sys
import uuid
from unittest.mock import MagicMock, patch

import pytest

# Add swarm client to path - use relative path from test file
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(TEST_DIR, "..", ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "swarm", "client"))
from client import JobQueue


class TestJobQueue:
    """Test JobQueue client functionality."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        mock = MagicMock()
        mock.ping.return_value = True
        return mock

    @patch("redis.Redis")
    def test_connect_success(self, mock_redis_class, mock_redis):
        """Test successful Redis connection."""
        mock_redis_class.return_value = mock_redis

        queue = JobQueue()
        result = queue.connect()

        assert result is True
        assert queue.redis_client is not None

    @patch("redis.Redis")
    def test_connect_failure(self, mock_redis_class):
        """Test failed Redis connection."""
        mock_redis_class.side_effect = Exception("Connection refused")

        queue = JobQueue()
        result = queue.connect()

        assert result is False

    @patch("redis.Redis")
    def test_enqueue_job(self, mock_redis_class, mock_redis):
        """Test enqueuing a job."""
        mock_redis_class.return_value = mock_redis

        queue = JobQueue()
        queue.connect()

        job_id = queue.enqueue("test:capability", {"key": "value"})

        assert job_id is not None
        assert isinstance(job_id, str)
        mock_redis.lpush.assert_called_once()

    @patch("redis.Redis")
    def test_enqueue_with_custom_id(self, mock_redis_class, mock_redis):
        """Test enqueuing with custom job ID."""
        mock_redis_class.return_value = mock_redis

        queue = JobQueue()
        queue.connect()

        custom_id = "custom-job-id"
        job_id = queue.enqueue("test:capability", {}, job_id=custom_id)

        assert job_id == custom_id

    @patch("redis.Redis")
    def test_get_result_immediate(self, mock_redis_class, mock_redis):
        """Test getting result immediately."""
        mock_redis_class.return_value = mock_redis
        mock_redis.get.return_value = json.dumps(
            {"status": "success", "result": {"data": "test"}},
        )

        queue = JobQueue()
        queue.connect()

        result = queue.get_result("test-job-id", timeout=0)

        assert result is not None
        assert result["status"] == "success"

    @patch("redis.Redis")
    def test_get_result_not_ready(self, mock_redis_class, mock_redis):
        """Test getting result when not ready."""
        mock_redis_class.return_value = mock_redis
        mock_redis.get.return_value = None

        queue = JobQueue()
        queue.connect()

        result = queue.get_result("test-job-id", timeout=0)

        assert result is None


class TestJobSerialization:
    """Test job serialization."""

    def test_job_json_structure(self):
        """Test job JSON structure."""
        job = {
            "job_id": str(uuid.uuid4()),
            "capability": "test:capability",
            "parameters": {"key": "value"},
            "enqueued_at": 1234567890.0,
        }

        serialized = json.dumps(job)
        deserialized = json.loads(serialized)

        assert "job_id" in deserialized
        assert "capability" in deserialized
        assert "parameters" in deserialized
        assert "enqueued_at" in deserialized
