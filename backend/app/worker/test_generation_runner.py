import asyncio
import json
import unittest
from types import SimpleNamespace

import httpx

from app.worker.generation_runner import GenerationRunnerConfig, run_generation_task
from app.worker.task_failures import mark_failed as persist_failed_task


class _FakeAsyncClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class GenerationRunnerTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.redis = object()
        self.ctx = {"redis": self.redis}
        self.status_calls = []
        self.progress_calls = []
        self.result_calls = []
        self.update_calls = []
        self.failed_calls = []
        self.timeout_calls = []
        self.sleep_calls = []
        self.db_error_updates = []
        self.refund_calls = []
        self.redis_error_calls = []
        self.terminal_status_calls = []
        self.user_id = 9
        self.monotonic_value = 0.0
        await self.patch_runner_dependencies()

    def build_config(self, **overrides):
        async def set_progress(redis, task_id, value):
            self.progress_calls.append((task_id, value))

        async def update_task(task_id, **kwargs):
            self.update_calls.append((task_id, kwargs))

        async def fetch_user_id(task_id):
            return self.user_id

        async def mark_failed(redis, task_id, message, **kwargs):
            self.failed_calls.append((task_id, message))

        async def mark_timeout(redis, task_id, message):
            self.timeout_calls.append((task_id, message))

        async def sleep_fn(seconds):
            self.sleep_calls.append(seconds)
            self.monotonic_value += seconds

        async def materialize_result(**kwargs):
            return SimpleNamespace(url="https://oss.example.com/final.png")

        base = GenerationRunnerConfig(
            media_type="image",
            provider_media="image",
            logger_name="test.generation_runner",
            client_timeout=60,
            max_wait_seconds=20,
            poll_interval_seconds=5,
            set_progress=set_progress,
            update_task=update_task,
            fetch_user_id=fetch_user_id,
            mark_failed=mark_failed,
            mark_timeout=mark_timeout,
            build_payload=lambda: {"prompt": "hi"},
            materialize_result=materialize_result,
            is_download_error=lambda exc: isinstance(exc, httpx.HTTPError),
            validate_inputs=lambda: None,
            config_missing_message=lambda: "missing key",
            task_missing_message=lambda: "missing task",
            create_failure_message=lambda exc: f"create failed: {exc}",
            create_parse_failure_message=lambda exc: f"create parse failed: {exc}",
            result_missing_message=lambda: "missing result url",
            provider_failed_message="provider failed",
            wait_timeout_message="wait timeout",
            request_timeout_message="request timeout",
            unexpected_failure_log_message="unexpected: %s",
            download_failure_message=lambda exc: f"download failed: {exc}",
            upload_failure_message=lambda exc: f"upload failed: {exc}",
            client_factory=lambda **kwargs: _FakeAsyncClient(),
            sleep_fn=sleep_fn,
            monotonic_fn=lambda: self.monotonic_value,
        )
        for key, value in overrides.items():
            setattr(base, key, value)
        return base

    async def patch_runner_dependencies(self):
        import app.worker.generation_runner as runner_module
        import app.worker.task_failures as failure_module

        self.original_set_task_status = runner_module.set_task_status
        self.original_set_task_result = runner_module.set_task_result
        self.original_toapis_key = runner_module.TOAPIS_KEY
        self.original_failure_update = failure_module.update_generation_task_in_db
        self.original_failure_refund = failure_module.refund_generation_credit
        self.original_failure_set_task_error = failure_module.set_task_error
        self.original_failure_set_task_status = failure_module.set_task_status

        async def fake_set_task_status(redis, media_type, task_id, status, *, ttl):
            self.status_calls.append((task_id, status, ttl))

        async def fake_set_task_result(redis, media_type, task_id, result_url):
            self.result_calls.append((task_id, result_url))

        async def fake_update_generation_task_in_db(media_type, task_id, **kwargs):
            if "error_message" in kwargs:
                self.db_error_updates.append((media_type, task_id, kwargs))

        async def fake_refund_generation_credit(media_type, task_id):
            self.refund_calls.append((media_type, task_id))
            return True

        async def fake_set_task_error(redis, media_type, task_id, message, *, ttl=3600):
            self.redis_error_calls.append((media_type, task_id, message, ttl))

        async def fake_failure_set_task_status(redis, media_type, task_id, status, *, ttl):
            self.terminal_status_calls.append((media_type, task_id, status, ttl))

        runner_module.set_task_status = fake_set_task_status
        runner_module.set_task_result = fake_set_task_result
        runner_module.TOAPIS_KEY = "test-key"
        failure_module.update_generation_task_in_db = fake_update_generation_task_in_db
        failure_module.refund_generation_credit = fake_refund_generation_credit
        failure_module.set_task_error = fake_set_task_error
        failure_module.set_task_status = fake_failure_set_task_status

    async def restore_runner_dependencies(self):
        import app.worker.generation_runner as runner_module
        import app.worker.task_failures as failure_module

        runner_module.set_task_status = self.original_set_task_status
        runner_module.set_task_result = self.original_set_task_result
        runner_module.TOAPIS_KEY = self.original_toapis_key
        failure_module.update_generation_task_in_db = self.original_failure_update
        failure_module.refund_generation_credit = self.original_failure_refund
        failure_module.set_task_error = self.original_failure_set_task_error
        failure_module.set_task_status = self.original_failure_set_task_status

    async def test_done_flow(self):
        poll_results = [
            {"status": "processing", "progress": 45},
            {"status": "success", "data": [{"url": "https://provider.example.com/final.png"}]},
        ]

        async def create_generation_fn(client, *, media, payload):
            return {"id": "provider-1"}

        async def fetch_generation_fn(client, *, media, provider_task_id):
            if poll_results:
                return poll_results.pop(0)
            return {"status": "success", "data": [{"url": "https://provider.example.com/final.png"}]}

        config = self.build_config(
            create_generation_fn=create_generation_fn,
            fetch_generation_fn=fetch_generation_fn,
            max_wait_seconds=15,
        )

        await run_generation_task(self.ctx, "task-1", config=config)

        self.assertEqual(self.failed_calls, [])
        self.assertEqual(self.timeout_calls, [])
        self.assertIn(("task-1", "processing", 7200), self.status_calls)
        self.assertIn(("task-1", "done", 86400), self.status_calls)
        self.assertIn(("task-1", 45), self.progress_calls)
        self.assertIn(("task-1", 100), self.progress_calls)
        self.assertIn(("task-1", "https://oss.example.com/final.png"), self.result_calls)

    async def test_create_failure(self):
        async def create_generation_fn(client, *, media, payload):
            raise httpx.ConnectError("boom")

        config = self.build_config(create_generation_fn=create_generation_fn)
        await run_generation_task(self.ctx, "task-2", config=config)
        self.assertEqual(self.failed_calls, [("task-2", "create failed: boom")])

    async def test_provider_failed(self):
        async def create_generation_fn(client, *, media, payload):
            return {"id": "provider-2"}

        async def fetch_generation_fn(client, *, media, provider_task_id):
            return {"status": "failed", "error": "bad prompt"}

        config = self.build_config(
            create_generation_fn=create_generation_fn,
            fetch_generation_fn=fetch_generation_fn,
        )
        await run_generation_task(self.ctx, "task-3", config=config)
        self.assertEqual(self.failed_calls, [("task-3", "bad prompt")])

    async def test_wait_timeout(self):
        async def create_generation_fn(client, *, media, payload):
            return {"id": "provider-3"}

        async def fetch_generation_fn(client, *, media, provider_task_id):
            return {"status": "processing", "progress": 10}

        config = self.build_config(
            create_generation_fn=create_generation_fn,
            fetch_generation_fn=fetch_generation_fn,
            max_wait_seconds=5,
            poll_interval_seconds=5,
        )
        await run_generation_task(self.ctx, "task-4", config=config)
        self.assertEqual(self.timeout_calls, [("task-4", "wait timeout")])

    async def test_oss_upload_failure(self):
        async def create_generation_fn(client, *, media, payload):
            return {"id": "provider-4"}

        async def fetch_generation_fn(client, *, media, provider_task_id):
            return {"status": "success", "data": [{"url": "https://provider.example.com/final.png"}]}

        async def materialize_result(**kwargs):
            raise RuntimeError("oss down")

        config = self.build_config(
            create_generation_fn=create_generation_fn,
            fetch_generation_fn=fetch_generation_fn,
            materialize_result=materialize_result,
            mark_failed=persist_failed_task,
            upload_failure_message=lambda exc: f"OSS 上传失败: {exc}",
        )
        await run_generation_task(self.ctx, "task-5", config=config)
        self.assertEqual(self.failed_calls, [])
        self.assertFalse(
            any(task_id == "task-5" and "error_message" in kwargs for task_id, kwargs in self.update_calls)
        )
        media_type, task_id, final_update = self.db_error_updates[-1]
        self.assertEqual((media_type, task_id), ("image", "task-5"))
        payload = json.loads(final_update["error_message"])
        self.assertEqual(payload["message"], "OSS 上传失败: oss down")
        self.assertEqual(payload["compensation"]["provider_task_id"], "provider-4")
        self.assertEqual(
            payload["compensation"]["final_url"],
            "https://provider.example.com/final.png",
        )
        self.assertEqual(final_update["status"], "failed")
        self.assertEqual(final_update["provider_task_id"], "provider-4")
        self.assertEqual(
            self.redis_error_calls[-1],
            ("image", "task-5", "OSS 上传失败: oss down", 3600),
        )
        self.assertEqual(self.terminal_status_calls[-1], ("image", "task-5", "failed", 3600))
        self.assertEqual(self.refund_calls[-1], ("image", "task-5"))

    async def test_download_failure(self):
        async def create_generation_fn(client, *, media, payload):
            return {"id": "provider-5"}

        async def fetch_generation_fn(client, *, media, provider_task_id):
            return {"status": "success", "data": [{"url": "https://provider.example.com/final.png"}]}

        async def materialize_result(**kwargs):
            raise httpx.ReadTimeout("slow")

        config = self.build_config(
            create_generation_fn=create_generation_fn,
            fetch_generation_fn=fetch_generation_fn,
            materialize_result=materialize_result,
        )
        await run_generation_task(self.ctx, "task-6", config=config)
        self.assertEqual(self.failed_calls, [("task-6", "download failed: slow")])

    async def asyncTearDown(self):
        await self.restore_runner_dependencies()


if __name__ == "__main__":
    unittest.main()
