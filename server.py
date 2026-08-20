"""HTTP service that logs IP addresses submitted by clients."""

from __future__ import annotations

import argparse
import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class IpHandler(BaseHTTPRequestHandler):
    server_version = "IpReceiver/1.0"

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/ip":
            self.send_error(404, "Use POST /ip")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 4096:
                raise ValueError("invalid request size")
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            claimed_ip = body["ip"]
            if not isinstance(claimed_ip, str) or not claimed_ip.strip():
                raise ValueError("ip must be a non-empty string")
        except (ValueError, KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            self.send_error(400, str(exc))
            return

        peer_ip = self.client_address[0]
        logging.info("client ip: %s (tcp peer: %s)", claimed_ip.strip(), peer_ip)
        response = json.dumps({"ok": True, "ip": claimed_ip.strip(), "peer_ip": peer_ip}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, *_args: object) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.getenv("IP_SERVER_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("IP_SERVER_PORT", "8080")))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    server = ThreadingHTTPServer((args.host, args.port), IpHandler)
    logging.info("listening on %s:%d", args.host, args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("stopping")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
