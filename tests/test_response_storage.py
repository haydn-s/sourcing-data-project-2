import base64
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError

from response_storage import GitHubConnectionError, GitHubStorage, LocalStorage, StorageError, build_storage


class StorageTests(unittest.TestCase):
    filename = "P01_VideoA_run-id_Assessment.csv"
    content = b"\xef\xbb\xbfrun_id,answer_letter\r\nrun-id,A\r\n"

    def test_local_write_is_in_raw_idempotent_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = LocalStorage(directory)
            path = storage.save(self.filename, self.content)
            self.assertEqual(path, f"data/raw/{self.filename}")
            self.assertEqual((Path(directory) / path).read_bytes(), self.content)
            self.assertEqual(storage.save(self.filename, self.content), path)
            with self.assertRaisesRegex(StorageError, "not overwritten"):
                storage.save(self.filename, b"different response")
            self.assertEqual(list((Path(directory) / "data/raw").iterdir()), [Path(directory) / path])
            with self.assertRaises(StorageError):
                storage.save("../escaped_Assessment.csv", self.content)

    def test_local_failure_does_not_publish_partial_response(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = LocalStorage(directory)
            with patch("response_storage.os.link", side_effect=PermissionError):
                with self.assertRaises(StorageError):
                    storage.save(self.filename, self.content)
            self.assertEqual(list(storage.directory.iterdir()), [])

    def github(self):
        return GitHubStorage("owner/repo", "responses", "test-token")

    def test_github_creates_csv_in_raw_on_configured_branch(self):
        storage = self.github()
        with patch.object(storage, "_request", side_effect=[(404, {}), (201, {})]) as request:
            self.assertEqual(storage.save(self.filename, self.content), f"data/raw/{self.filename}")
        get_args, put_args = [call.args for call in request.call_args_list]
        self.assertIn("/contents/data/raw/", get_args[1])
        self.assertTrue(get_args[1].endswith("?ref=responses"))
        self.assertEqual(put_args[0], "PUT")
        self.assertEqual(put_args[2]["branch"], "responses")
        self.assertNotIn("sha", put_args[2])
        self.assertEqual(base64.b64decode(put_args[2]["content"]), self.content)

    def test_retry_after_uncertain_write_recognizes_the_saved_run(self):
        storage = self.github()
        existing = {"content": base64.b64encode(self.content).decode()}
        with patch.object(storage, "_request", side_effect=[
            (404, {}), GitHubConnectionError("timeout"), (200, existing),
        ]) as request, patch("response_storage.time.sleep"):
            storage.save(self.filename, self.content)
        self.assertEqual([call.args[0] for call in request.call_args_list], ["GET", "PUT", "GET"])

    def test_github_conflicts_and_transient_reads_are_retried(self):
        storage = self.github()
        with patch.object(storage, "_request", side_effect=[
            (503, {}), (404, {}), (409, {}), (404, {}), (201, {}),
        ]), patch("response_storage.time.sleep"):
            storage.save(self.filename, self.content)

    def test_github_rejects_overwrites_and_denied_writes(self):
        storage = self.github()
        with patch.object(storage, "_request", return_value=(200, {"content": "ZGlmZmVyZW50"})) as request:
            with self.assertRaisesRegex(StorageError, "not overwritten"):
                storage.save(self.filename, self.content)
            self.assertEqual(request.call_count, 1)
        with patch.object(storage, "_request", side_effect=[(404, {}), (403, {})]):
            with self.assertRaisesRegex(StorageError, "HTTP 403"):
                storage.save(self.filename, self.content)

    def test_request_uses_server_side_token_and_a_timeout(self):
        storage = self.github()
        with patch("response_storage.urlopen", side_effect=URLError("offline")) as request:
            with self.assertRaises(GitHubConnectionError):
                storage._request("GET", "https://api.github.com/repos/owner/repo/contents/data/raw")
        self.assertEqual(request.call_args.kwargs["timeout"], 10)
        self.assertEqual(request.call_args.args[0].get_header("Authorization"), "Bearer test-token")

    def test_hosting_requires_credentials_instead_of_silently_saving_locally(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(StorageError):
                build_storage({})
            self.assertIsInstance(build_storage({"storage": {"backend": "local"}}), LocalStorage)


if __name__ == "__main__":
    unittest.main()
