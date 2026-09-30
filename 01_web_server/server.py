"""Simple HTTP/1.1 web server (Chapter 2, Assignment 1).
Usage: python server.py [port]   -> then open http://localhost:8080/index.html
Serves files from ./www ; returns 404 if missing. One thread per connection."""
import socket, sys, threading, os, mimetypes

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "www")

def handle(conn):
    try:
        data = conn.recv(4096).decode(errors="replace")
        if not data:
            return
        method, path, _ = data.split("\r\n")[0].split(" ", 2)
        if path == "/":
            path = "/index.html"
        full = os.path.normpath(os.path.join(ROOT, path.lstrip("/")))
        if method != "GET" or not full.startswith(ROOT) or not os.path.isfile(full):
            body = b"<h1>404 Not Found</h1>"
            head = "HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n"
        else:
            body = open(full, "rb").read()
            ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
            head = f"HTTP/1.1 200 OK\r\nContent-Type: {ctype}\r\n"
        head += f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n"
        conn.sendall(head.encode() + body)
    except ValueError:
        conn.sendall(b"HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n")
    finally:
        conn.close()

def main(port=8080):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("", port)); s.listen(5)
    print(f"Serving {ROOT} on port {port}")
    while True:
        conn, _ = s.accept()
        threading.Thread(target=handle, args=(conn,), daemon=True).start()

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 8080)
