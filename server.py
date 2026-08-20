import socket
import json
from urllib.request import urlopen
from urllib.parse import quote


HOST = "0.0.0.0"
PORT = 7213


def get_location(ip):
    """Return approximate location data from ip-api.com."""
    try:
        url = f"http://ip-api.com/json/{quote(ip)}?fields=status,message,country,regionName,city,lat,lon,timezone,isp"
        with urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("status") != "success":
            return f"location unavailable ({data.get('message', 'unknown error')})"

        return (
            f"{data.get('country', '?')}, {data.get('regionName', '?')}, "
            f"{data.get('city', '?')} | "
            f"coordinates: {data.get('lat', '?')}, {data.get('lon', '?')} | "
            f"timezone: {data.get('timezone', '?')} | ISP: {data.get('isp', '?')}"
        )
    except Exception as error:
        return f"location lookup failed ({error})"


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()

    print(f"Server listening on port {PORT}...")

    while True:
        connection, address = server.accept()
        with connection:
            client_ip, client_port = address
            print(f"Connected: {client_ip}:{client_port}")
            print(f"Location: {get_location(client_ip)}")
            connection.sendall(b"Connected to server.\n")
