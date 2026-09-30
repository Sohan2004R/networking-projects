"""UDP ping server: echoes uppercase, randomly drops ~30% of packets."""
import random, socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("", 12000))
print("UDP ping server on port 12000")
while True:
    msg, addr = s.recvfrom(1024)
    if random.randint(0, 9) < 3:
        continue  # simulate packet loss
    s.sendto(msg.upper(), addr)
