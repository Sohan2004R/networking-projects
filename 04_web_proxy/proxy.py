"""HTTP caching web proxy (Chapter 2, Assignment 4). Handles plain HTTP GET only.
Usage: python proxy.py [port]; set browser proxy to localhost:8888, visit http://example.com"""
import socket, sys, threading
from urllib.parse import urlsplit

cache, lock = {}, threading.Lock()

def handle(client):
    try:
        req = client.recv(8192).decode(errors="replace")
        line = req.split("\r\n")[0]
        method, url, _ = line.split(" ", 2)
        if method != "GET":
            client.sendall(b"HTTP/1.1 501 Not Implemented\r\n\r\n"); return
        u = urlsplit(url)
        host, port = u.hostname, u.port or 80
        path = (u.path or "/") + (f"?{u.query}" if u.query else "")
        key = (host, port, path)
        with lock:
            hit = cache.get(key)
        if hit:
            print("CACHE HIT ", url); client.sendall(hit); return
        print("CACHE MISS", url)
        up = socket.create_connection((host, port), timeout=10)
        up.sendall(f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n".encode())
        chunks = []
        while (d := up.recv(4096)):
            chunks.append(d)
        up.close()
        resp = b"".join(chunks)
        if resp.startswith(b"HTTP/1.1 200") or resp.startswith(b"HTTP/1.0 200"):
            with lock:
                cache[key] = resp
        client.sendall(resp)
    except Exception as e:
        print("error:", e)
        try: client.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
        except OSError: pass
    finally:
        client.close()

def main(port=8888):
    s = socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("", port)); s.listen(20)
    print(f"Proxy on port {port}")
    while True:
        c, _ = s.accept()
        threading.Thread(target=handle, args=(c,), daemon=True).start()

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 8888)
