#!/usr/bin/env python3
"""Serve the dashboard and expose a local, read-only market refresh endpoint."""

import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from fetch_shioaji_data import fetch_shioaji


ROOT = Path(__file__).resolve().parent


class DashboardHandler(SimpleHTTPRequestHandler):
    """Static file handler plus POST /api/refresh for local Shioaji refreshes."""

    server_version = "TaiwanStockDashboard/1.0"

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        if self.path == "/api/refresh":
            self.send_response(204)
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            return
        self.send_error(404)

    def do_POST(self):
        if self.path != "/api/refresh":
            self.send_error(404)
            return

        try:
            payload = fetch_shioaji()
            self._send_json(200, payload)
        except Exception as exc:
            self._send_json(
                503,
                {
                    "error": f"{type(exc).__name__}: {exc}",
                    "message": "No fresh Shioaji/TWSE quote was written; existing data was preserved.",
                },
            )

    def _send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:8765")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format_string, *args):
        print(f"[dashboard] {self.address_string()} - {format_string % args}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1", help="Local bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Local HTTP port (default: 8765)")
    args = parser.parse_args()

    handler = partial(DashboardHandler, directory=str(ROOT))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Dashboard: http://{args.host}:{args.port}/")
    print("POST /api/refresh uses read-only Shioaji snapshots and TWSE MIS cross-checks.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard server stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
