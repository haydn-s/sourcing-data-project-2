"""Save a completed run locally or commit it to data/raw on GitHub."""

import base64
import json
import os
from pathlib import Path
import re
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from assessment import ROOT


RAW_DIRECTORY = "data/raw"


class StorageError(Exception):
    """A response could not be durably saved; the same run can be retried."""


class GitHubConnectionError(StorageError):
    """The request may have reached GitHub; retry by checking the run first."""


def validate_filename(filename):
    if not filename.endswith("_Assessment.csv") or Path(filename).name != filename or "\\" in filename:
        raise StorageError("Invalid response filename.")


class LocalStorage:
    def __init__(self, root=ROOT):
        self.directory = Path(root) / RAW_DIRECTORY

    def save(self, filename, content):
        validate_filename(filename)
        target = self.directory / filename
        temporary = None
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            # Publish a fully written file atomically, without replacing another run.
            with tempfile.NamedTemporaryFile(dir=self.directory, delete=False) as handle:
                temporary = Path(handle.name)
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temporary, target)
            except FileExistsError:
                if target.read_bytes() != content:
                    raise StorageError("An existing response has different contents; it was not overwritten.")
        except OSError as error:
            raise StorageError("Could not write the response to data/raw. Check the server's folder permissions.") from error
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return f"{RAW_DIRECTORY}/{filename}"


class GitHubStorage:
    def __init__(self, repository, branch, token):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
            raise StorageError("Set github.repository to owner/repository in Streamlit Secrets.")
        if not branch.strip() or not token.strip() or token.startswith("REPLACE_"):
            raise StorageError("Set github.branch and a GitHub token in Streamlit Secrets.")
        self.repository, self.branch, self._token = repository, branch, token

    def _request(self, method, url, body=None):
        request = Request(url, method=method, headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._token}",
            "X-GitHub-Api-Version": "2026-03-10",
            "User-Agent": "aipi-510-assessment",
            "Content-Type": "application/json",
        }, data=json.dumps(body).encode() if body is not None else None)
        try:
            with urlopen(request, timeout=10) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, {}
        except (URLError, OSError, ValueError) as error:
            raise GitHubConnectionError("Could not reach GitHub. Please try saving again.") from error

    def save(self, filename, content):
        validate_filename(filename)
        path = f"{RAW_DIRECTORY}/{filename}"
        url = f"https://api.github.com/repos/{self.repository}/contents/{quote(path, safe='/')}"
        lookup = f"{url}?{urlencode({'ref': self.branch})}"
        body = {
            "message": f"Add assessment response {filename}",
            "content": base64.b64encode(content).decode("ascii"),
            "branch": self.branch,
        }
        for attempt in range(3):
            try:
                status, existing = self._request("GET", lookup)
                if status == 200:
                    if base64.b64decode(existing.get("content", "")) == content:
                        return path
                    raise StorageError("An existing response has different contents; it was not overwritten.")
                if status == 429 or status >= 500:
                    raise GitHubConnectionError("GitHub is temporarily unavailable.")
                if status != 404:
                    raise StorageError(f"GitHub could not read responses (HTTP {status}). Check the token, repository and branch.")
                # Omitting sha means this request can create a file but never overwrite one.
                status, _ = self._request("PUT", url, body)
                if status == 201:
                    return path
                if status not in (409, 422, 429) and status < 500:
                    raise StorageError(f"GitHub could not save the response (HTTP {status}). Check Contents write permission and branch rules.")
            except GitHubConnectionError:
                # Retry uncertain network outcomes; GET detects a successful earlier write.
                pass
            if attempt < 2:
                time.sleep(0.5 * (attempt + 1))
        raise StorageError("GitHub did not confirm the save. Please try saving again.")


def build_storage(secrets, *, root=ROOT):
    # Hosted apps require durable storage unless local mode is explicitly selected.
    backend = os.environ.get("QUIZ_STORAGE", secrets.get("storage", {}).get("backend", "github"))
    if backend == "local":
        return LocalStorage(root)
    if backend != "github":
        raise StorageError("storage.backend must be github or local.")
    github = secrets.get("github", {})
    return GitHubStorage(
        github.get("repository", "haydn-s/sourcing-data-project-2"),
        github.get("branch", "data-collection-scaffolding"),
        github.get("token", ""),
    )
