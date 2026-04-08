"""Static HTTP server for the benchmark site."""

from __future__ import annotations

import argparse
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread


CONTENT_TYPES: dict[str, str] = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
}


class BenchmarkSiteHandler(SimpleHTTPRequestHandler):
    """Serves static files from the public/ directory."""

    def __init__(self, *args: object, public_dir: str, **kwargs: object) -> None:
        self._public_dir = public_dir
        super().__init__(*args, directory=public_dir, **kwargs)

    def log_message(self, format: str, *args: object) -> None:
        pass  # Suppress request logs

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def start_server(
    port: int = 4173,
    host: str = "127.0.0.1",
    public_dir: str | None = None,
) -> dict:
    """Start the benchmark site server.

    Returns a dict with 'server', 'url', and 'thread' keys.
    """
    if public_dir is None:
        public_dir = os.path.join(os.path.dirname(__file__), "public")

    def handler(*args: object, **kwargs: object) -> BenchmarkSiteHandler:
        return BenchmarkSiteHandler(*args, public_dir=public_dir, **kwargs)

    server = HTTPServer((host, port), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return {
        "server": server,
        "url": f"http://{host}:{port}",
        "thread": thread,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark site server")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 4173)))
    args = parser.parse_args()

    handle = start_server(port=args.port)
    print(f"Benchmark site listening at {handle['url']}")
    try:
        handle["thread"].join()
    except KeyboardInterrupt:
        handle["server"].shutdown()


if __name__ == "__main__":
    main()
