"""ICMP Ping (Chapter 5). Needs raw sockets: run with sudo / Administrator.
Usage: sudo python ping.py google.com [count]"""
import os, select, socket, struct, sys, time, statistics

def checksum(data):
    if len(data) % 2: data += b"\0"
    s = sum(struct.unpack("!%dH" % (len(data) // 2), data))
    s = (s >> 16) + (s & 0xFFFF); s += s >> 16
    return ~s & 0xFFFF

def ping_once(sock, addr, ident, seq, timeout=1.0):
    payload = struct.pack("!d", time.time()) + b"abcdefghijklmnop"
    hdr = struct.pack("!BBHHH", 8, 0, 0, ident, seq)          # type 8 = echo request
    hdr = struct.pack("!BBHHH", 8, 0, checksum(hdr + payload), ident, seq)
    sock.sendto(hdr + payload, (addr, 0))
    deadline = time.time() + timeout
    while (left := deadline - time.time()) > 0:
        if not select.select([sock], [], [], left)[0]: break
        pkt, src = sock.recvfrom(1024)
        t = time.time()
        icmp = pkt[(pkt[0] & 0x0F) * 4:]                       # skip IP header
        typ, code, _, pid, pseq = struct.unpack("!BBHHH", icmp[:8])
        if typ == 0 and pid == ident and pseq == seq:          # type 0 = echo reply
            return (t - struct.unpack("!d", icmp[8:16])[0]) * 1000, len(pkt), pkt[8]
        if typ == 3: return "unreachable", 0, 0
    return None, 0, 0

def main(host, count=4):
    addr = socket.gethostbyname(host)
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))
    ident = os.getpid() & 0xFFFF
    print(f"PING {host} ({addr})")
    rtts = []
    for seq in range(1, count + 1):
        rtt, size, ttl = ping_once(sock, addr, ident, seq)
        if isinstance(rtt, float):
            rtts.append(rtt); print(f"{size} bytes from {addr}: seq={seq} ttl={ttl} time={rtt:.2f} ms")
        else:
            print(f"seq={seq}: {'destination unreachable' if rtt else 'request timed out'}")
        time.sleep(1)
    print(f"\n--- {host} ping statistics ---")
    print(f"{count} sent, {len(rtts)} received, {100*(count-len(rtts))//count}% loss")
    if rtts:
        sd = statistics.pstdev(rtts)
        print(f"rtt min/avg/max/stddev = {min(rtts):.2f}/{sum(rtts)/len(rtts):.2f}/{max(rtts):.2f}/{sd:.2f} ms")

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 4)
