"""Raw-socket SMTP client (Chapter 2, Assignment 3). No smtplib: we speak SMTP by hand.
Setup (Gmail): enable 2FA, create an *App Password*, then:
    export SMTP_USER=you@gmail.com SMTP_PASS=your_app_password
    python mail_client.py friend@example.com "Subject" "Body text"
NEVER commit your password to GitHub."""
import base64, os, socket, ssl, sys

HOST, PORT = "smtp.gmail.com", 587

def send(f, cmd, expect):
    if cmd is not None:
        print("C:", cmd.strip()); f["sock"].sendall(cmd.encode())
    while True:  # handle multi-line replies (250-...)
        line = f["r"].readline().decode().rstrip()
        print("S:", line)
        if line[3:4] != "-":
            break
    if not line.startswith(expect):
        raise RuntimeError(f"Expected {expect}, got: {line}")

def main(to, subject, body):
    user, pw = os.environ["SMTP_USER"], os.environ["SMTP_PASS"]
    sock = socket.create_connection((HOST, PORT), timeout=15)
    f = {"sock": sock, "r": sock.makefile("rb")}
    send(f, None, "220")
    send(f, "EHLO client.local\r\n", "250")
    send(f, "STARTTLS\r\n", "220")
    sock = ssl.create_default_context().wrap_socket(sock, server_hostname=HOST)
    f = {"sock": sock, "r": sock.makefile("rb")}
    send(f, "EHLO client.local\r\n", "250")
    send(f, "AUTH LOGIN\r\n", "334")
    send(f, base64.b64encode(user.encode()).decode() + "\r\n", "334")
    send(f, base64.b64encode(pw.encode()).decode() + "\r\n", "235")
    send(f, f"MAIL FROM:<{user}>\r\n", "250")
    send(f, f"RCPT TO:<{to}>\r\n", "250")
    send(f, "DATA\r\n", "354")
    msg = f"From: {user}\r\nTo: {to}\r\nSubject: {subject}\r\n\r\n{body}\r\n.\r\n"
    send(f, msg, "250")
    send(f, "QUIT\r\n", "221")
    sock.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
