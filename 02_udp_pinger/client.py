"""UDP ping client: 10 pings, 1s timeout, RTT stats.  Usage: python client.py [host] [port]"""
import socket, sys, time
host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
port = int(sys.argv[2]) if len(sys.argv) > 2 else 12000
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.settimeout(1)
rtts = []
for seq in range(1, 11):
    t0 = time.time()
    s.sendto(f"Ping {seq} {t0}".encode(), (host, port))
    try:
        reply, _ = s.recvfrom(1024)
        rtt = (time.time() - t0) * 1000
        rtts.append(rtt)
        print(f"Reply from {host}: {reply.decode()}  RTT={rtt:.3f} ms")
    except socket.timeout:
        print(f"Ping {seq}: Request timed out")
loss = (10 - len(rtts)) * 10
print(f"\n10 sent, {len(rtts)} received, {loss}% loss")
if rtts:
    print(f"RTT min/avg/max = {min(rtts):.3f}/{sum(rtts)/len(rtts):.3f}/{max(rtts):.3f} ms")
