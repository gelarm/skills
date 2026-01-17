"""Synchronous HTTP client for GIMS Automation API."""

import os
import re
import sys
import time
from typing import Any, Iterator

import httpx


class GimsApiError(Exception):
    """Exception raised when GIMS API returns an error."""

    def __init__(self, status_code: int, message: str, detail: str | None = None):
        self.status_code = status_code
        self.message = message
        self.detail = detail
        super().__init__(f"GIMS API Error ({status_code}): {message}")


class GimsClient:
    """Synchronous HTTP client for GIMS Automation API."""

    def __init__(self):
        config = self._load_config()
        self.base_url = config["url"].rstrip("/") + "/automation"
        self.gims_url = config["url"].rstrip("/")
        self._access_token = config["access_token"]
        self._refresh_token = config["refresh_token"]
        self.verify_ssl = config.get("verify_ssl", True)
        self.timeout = 30.0

    def _load_config(self) -> dict:
        """Load configuration from environment variables."""
        config = {}
        config["url"] = os.environ.get("GIMS_URL", "")
        config["access_token"] = os.environ.get("GIMS_ACCESS_TOKEN", "")
        config["refresh_token"] = os.environ.get("GIMS_REFRESH_TOKEN", "")

        verify_ssl = os.environ.get("GIMS_VERIFY_SSL", "true").lower()
        config["verify_ssl"] = verify_ssl not in ("false", "0", "no", "off")

        # Validate
        if not config["url"]:
            raise GimsApiError(0, "Configuration error", "GIMS_URL not set")
        if not config["access_token"]:
            raise GimsApiError(0, "Configuration error", "GIMS_ACCESS_TOKEN not set")
        if not config["refresh_token"]:
            raise GimsApiError(0, "Configuration error", "GIMS_REFRESH_TOKEN not set")

        return config

    def _refresh_access_token(self) -> None:
        """Refresh the access token using the refresh token."""
        refresh_url = f"{self.gims_url}/security/token/refresh/"

        with httpx.Client(timeout=self.timeout, verify=self.verify_ssl) as client:
            response = client.post(
                refresh_url,
                json={"refresh": self._refresh_token},
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 401:
                raise GimsApiError(
                    401,
                    "Authentication failed",
                    "Refresh token is invalid. Get new tokens from GIMS.",
                )

            if response.status_code != 200:
                raise GimsApiError(
                    response.status_code,
                    "Token refresh failed",
                    response.text[:500],
                )

            data = response.json()
            self._access_token = data["access"]
            if "refresh" in data:
                self._refresh_token = data["refresh"]

    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle API response, raising errors if needed."""
        if response.status_code == 401:
            raise GimsApiError(401, "Authentication failed", "Token expired")
        if response.status_code == 403:
            raise GimsApiError(403, "Permission denied", "Insufficient permissions")
        if response.status_code == 404:
            raise GimsApiError(404, "Not found", "Resource not found")
        if response.status_code >= 400:
            try:
                data = response.json()
                detail = data.get("detail", str(data))
            except Exception:
                detail = self._sanitize_error_response(response)
            raise GimsApiError(response.status_code, "API error", detail)

        if response.status_code == 204:
            return None

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            raise GimsApiError(
                response.status_code,
                "Invalid response format",
                f"Expected JSON, got '{content_type}'",
            )

        return response.json()

    def _sanitize_error_response(self, response: httpx.Response) -> str:
        """Sanitize error response to prevent HTML garbage."""
        content_type = response.headers.get("content-type", "")
        text = response.text

        if "text/html" in content_type or text.strip().startswith(("<!DOCTYPE", "<html")):
            title_match = re.search(r"<title[^>]*>([^<]+)</title>", text, re.IGNORECASE)
            if title_match:
                return f"Server returned HTML error: {title_match.group(1).strip()}"
            return "Server returned HTML error page"

        if len(text) > 500:
            return f"{text[:500]}... (truncated)"

        return text

    def request(self, method: str, path: str, **kwargs) -> Any:
        """Make an HTTP request with automatic token refresh on 401."""
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=self.timeout, verify=self.verify_ssl) as client:
            response = client.request(method, url, headers=headers, **kwargs)

            if response.status_code == 401:
                self._refresh_access_token()
                headers["Authorization"] = f"Bearer {self._access_token}"
                response = client.request(method, url, headers=headers, **kwargs)

            return self._handle_response(response)

    def stream_sse(self, url: str, timeout: float) -> Iterator[str]:
        """Stream SSE events from a URL.

        Args:
            url: The SSE stream URL (can be relative or absolute).
            timeout: Total timeout in seconds.

        Yields:
            JSON content strings from SSE data events.
        """
        if url.startswith("/"):
            url = f"{self.gims_url}{url}"

        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "text/event-stream",
        }

        start_time = time.monotonic()
        read_timeout = 5.0  # Small read timeout for periodic checks

        while True:
            if time.monotonic() - start_time >= timeout:
                return

            try:
                with httpx.Client(
                    timeout=httpx.Timeout(read_timeout, connect=10.0),
                    verify=self.verify_ssl,
                ) as client:
                    with client.stream("GET", url, headers=headers) as response:
                        if response.status_code == 401:
                            self._refresh_access_token()
                            headers["Authorization"] = f"Bearer {self._access_token}"
                            continue

                        if response.status_code != 200:
                            raise GimsApiError(
                                response.status_code,
                                "Failed to connect to log stream",
                                f"HTTP {response.status_code}",
                            )

                        for line in response.iter_lines():
                            if time.monotonic() - start_time >= timeout:
                                return
                            if line.startswith("data:"):
                                yield line[5:]
                    return
            except httpx.ReadTimeout:
                if time.monotonic() - start_time >= timeout:
                    return
                continue
            except httpx.RequestError as e:
                raise GimsApiError(0, "SSE connection error", str(e)) from e


def print_error(message: str) -> None:
    """Print error message to stderr."""
    print(f"Error: {message}", file=sys.stderr)


def print_json(data: Any) -> None:
    """Print data as formatted JSON."""
    import json
    print(json.dumps(data, indent=2, ensure_ascii=False))
