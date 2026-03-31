import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import duckdb
import requests

from ingest import dlt_api_source


class _FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")

    def json(self):
        return self._payload


class DltApiSourceTests(unittest.TestCase):
    def test_posts_resource_uses_timeout_and_returns_payload(self):
        payload = [{"id": 1, "userId": 2, "title": "hello", "body": "world"}]
        with mock.patch.object(
            dlt_api_source.requests,
            "get",
            return_value=_FakeResponse(payload),
        ) as mock_get:
            rows = dlt_api_source.fetch_json(dlt_api_source.get_api_base_url(), "posts")

        self.assertEqual(rows, payload)
        mock_get.assert_called_once_with(
            f"{dlt_api_source.get_api_base_url()}/posts",
            timeout=30,
        )

    def test_get_api_base_url_strips_trailing_slash(self):
        with mock.patch.dict(
            dlt_api_source.os.environ,
            {"API_BASE_URL": "https://example.com/"},
            clear=False,
        ):
            self.assertEqual(dlt_api_source.get_api_base_url(), "https://example.com")

    def test_fetch_json_raises_http_errors(self):
        with mock.patch.object(
            dlt_api_source.requests,
            "get",
            return_value=_FakeResponse([], status_code=500),
        ):
            with self.assertRaises(requests.HTTPError):
                dlt_api_source.fetch_json(dlt_api_source.get_api_base_url(), "users")

    def test_main_prints_structured_error_and_exits_one(self):
        fake_pipeline = mock.Mock()
        fake_pipeline.run.side_effect = requests.ConnectionError("boom")
        with mock.patch.object(dlt_api_source.dlt, "pipeline", return_value=fake_pipeline):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                with self.assertRaises(SystemExit) as exc:
                    dlt_api_source.main()

        self.assertEqual(exc.exception.code, 1)
        payload = json.loads(stdout.getvalue().strip())
        self.assertEqual(payload["level"], "ERROR")
        self.assertEqual(payload["pipeline"], "jsonplaceholder")
        self.assertIn("boom", payload["error"])

    def test_pipeline_is_idempotent_for_same_api_payload(self):
        posts_payload = [
            {"id": 1, "userId": 1, "title": "post 1", "body": "body 1"},
            {"id": 2, "userId": 1, "title": "post 2", "body": "body 2"},
        ]
        users_payload = [
            {
                "id": 1,
                "name": "Ada Lovelace",
                "username": "adal",
                "email": "ada@example.com",
                "phone": "123",
                "website": "example.com",
                "address": {"city": "London"},
                "company": {"name": "Analytical Engines"},
            }
        ]

        def fake_get(url, timeout):
            self.assertEqual(timeout, 30)
            if url.endswith("/posts"):
                return _FakeResponse(posts_payload)
            if url.endswith("/users"):
                return _FakeResponse(users_payload)
            raise AssertionError(f"Unexpected URL {url}")

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "api.duckdb"
            with mock.patch.dict(
                dlt_api_source.os.environ,
                {"DBT_DUCKDB_PATH": str(db_path)},
                clear=False,
            ):
                with mock.patch.object(dlt_api_source.requests, "get", side_effect=fake_get):
                    dlt_api_source.main()
                    dlt_api_source.main()

            conn = duckdb.connect(str(db_path), read_only=True)
            try:
                posts_count = conn.execute("SELECT COUNT(*) FROM bronze.posts").fetchone()[0]
                users_count = conn.execute("SELECT COUNT(*) FROM bronze.users").fetchone()[0]
                post_columns = {
                    row[0]
                    for row in conn.execute(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_schema='bronze' AND table_name='posts'"
                    ).fetchall()
                }
                user_columns = {
                    row[0]
                    for row in conn.execute(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_schema='bronze' AND table_name='users'"
                    ).fetchall()
                }
            finally:
                conn.close()

        self.assertEqual(posts_count, 2)
        self.assertEqual(users_count, 1)
        self.assertIn("_dlt_load_id", post_columns)
        self.assertIn("_dlt_id", post_columns)
        self.assertIn("_dlt_load_id", user_columns)
        self.assertIn("_dlt_id", user_columns)


if __name__ == "__main__":
    unittest.main()
