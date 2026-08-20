"""HTTP service that logs IP addresses submitted by clients."""

from __future__ import annotations

import argparse
import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
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
        location = lookup_location(peer_ip)
        logging.info(
            "client ip: %s (tcp peer: %s), location: %s",
            claimed_ip.strip(), peer_ip, format_location(location),
        )
        response = json.dumps(
            {"ok": True, "ip": claimed_ip.strip(), "peer_ip": peer_ip, "location": location}
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, *_args: object) -> None:
        return


def lookup_location(ip: str) -> dict[str, object] | None:
    """Look up a public IP without making geolocation availability critical."""
    if not os.getenv("IP_GEOLOCATION_ENABLED", "true").lower() in {"1", "true", "yes"}:
        return None
    url = f"https://ipwho.is/{urllib.parse.quote(ip, safe='')}"
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            data = json.loads(response.read().decode("utf-8"))
        if not data.get("success"):
            logging.warning("geolocation lookup failed for %s: %s", ip, data.get("message", "unknown error"))
            return None
        return {
            "country": data.get("country"),
            "region": data.get("region"),
            "city": data.get("city"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "timezone": data.get("timezone", {}).get("id"),
        }
    except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError) as exc:
        logging.warning("geolocation lookup failed for %s: %s", ip, exc)
        return None


def format_location(location: dict[str, object] | None) -> str:
    if not location:
        return "unavailable"
    parts = [location.get("country"), location.get("region"), location.get("city")]
    place = ", ".join(str(part) for part in parts if part)
    coordinates = f"{location.get('latitude')}, {location.get('longitude')}"
    return f"{place} ({coordinates})" if place else coordinates


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
