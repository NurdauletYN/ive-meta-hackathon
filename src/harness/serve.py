"""Tiny static file server for a design-run directory (gallery + web builds)."""

from __future__ import annotations

import http.server
import os
from pathlib import Path


def serve(directory: Path, port: int = 8765) -> None:
    os.chdir(directory)
    handler = http.server.SimpleHTTPRequestHandler
    with http.server.HTTPServer(("127.0.0.1", port), handler) as httpd:
        print(f"serving {directory} at http://127.0.0.1:{port}/gallery.html")
        httpd.serve_forever()
