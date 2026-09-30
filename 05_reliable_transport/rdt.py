"""Reliable data transfer over an unreliable channel (Chapter 3 lab).
Event-driven simulator (like the book's emulator) with packet loss + corruption.
  python rdt.py --protocol gbn --window 8 --loss 0.2 --corrupt 0.1 --messages 30
  python rdt.py --protocol stopwait ...      (alternating-bit / rdt3.0 style, window = 1)
Sequence numbers are absolute, so stop-and-wait == GBN with window 1."""
import argparse, heapq, random, zlib

class Sim:
    def __init__(self, a):
        self.a, self.t, self.q, self.n = a, 0.0, [], 0
        self.timer_gen, self.timer_on = 0, False
        # sender state
        self.window = 1 if a.protocol == "stopwait" else a.window
        self.base = self.nxt = 0
        self.msgs = [f"message-{i}" for i in range(a.messages)]
        # receiver state
        self.expected, self.delivered = 0, []
        self.stats = dict(sent=0, retx=0, lost=0, corrupted=0)

    def at(self, dt, kind, data=None):
        self.n += 1; heapq.heappush(self.q, (self.t + dt, self.n, kind, data))

    @staticmethod
    def chk(seq, ack, data): return zlib.crc32(f"{seq}|{ack}|{data}".encode())

    def mk(self, seq, ack, data=""): return dict(seq=seq, ack=ack, data=data, ck=self.chk(seq, ack, data))
    def ok(self, p): return p["ck"] == self.chk(p["seq"], p["ack"], p["data"])

    def channel(self, pkt, dest):
        if random.random() < self.a.loss:
            self.stats["lost"] += 1; return
        pkt = dict(pkt)
        if random.random() < self.a.corrupt:
            pkt["data"] += "#"; pkt["seq"] ^= 1; self.stats["corrupted"] += 1
        self.at(random.uniform(1, 5), dest, pkt)

    # --- sender (A) ---
    def start_timer(self):
        self.timer_gen += 1; self.timer_on = True
        self.at(self.a.timeout, "timeout", self.timer_gen)
    def stop_timer(self): self.timer_on = False; self.timer_gen += 1

    def send_new(self):
        while self.nxt < self.base + self.window and self.nxt < len(self.msgs):
            self.channel(self.mk(self.nxt, -1, self.msgs[self.nxt]), "B"); self.stats["sent"] += 1
            if self.base == self.nxt: self.start_timer()
            self.nxt += 1

    def on_ack(self, p):
        if not self.ok(p) or p["ack"] < self.base: return   # corrupt/duplicate ACK: ignore
        self.base = p["ack"] + 1                              # cumulative ACK
        self.stop_timer()
        if self.base != self.nxt: self.start_timer()
        self.send_new()

    def on_timeout(self, gen):
        if gen != self.timer_gen or not self.timer_on: return
        self.start_timer()
        for s in range(self.base, self.nxt):                  # Go-Back-N: resend whole window
            self.channel(self.mk(s, -1, self.msgs[s]), "B"); self.stats["retx"] += 1

    # --- receiver (B) ---
    def on_data(self, p):
        if self.ok(p) and p["seq"] == self.expected:
            self.delivered.append(p["data"]); self.expected += 1
        if self.expected > 0:                                 # (re)ACK last in-order packet
            self.channel(self.mk(-1, self.expected - 1), "A")

    def run(self):
        self.send_new()
        while self.q and self.t < 1e6 and len(self.delivered) < len(self.msgs) or (self.q and self.base < len(self.msgs)):
            self.t, _, kind, data = heapq.heappop(self.q)
            {"A": self.on_ack, "B": self.on_data, "timeout": self.on_timeout}[kind](data)
        return self.delivered == self.msgs

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", choices=["gbn", "stopwait"], default="gbn")
    ap.add_argument("--window", type=int, default=8)
    ap.add_argument("--loss", type=float, default=0.2)
    ap.add_argument("--corrupt", type=float, default=0.1)
    ap.add_argument("--messages", type=int, default=30)
    ap.add_argument("--timeout", type=float, default=20)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args(); random.seed(a.seed)
    s = Sim(a); ok = s.run()
    print(f"protocol={a.protocol} window={s.window} loss={a.loss} corrupt={a.corrupt}")
    print(f"delivered {len(s.delivered)}/{a.messages} in order: {ok}  time={s.t:.0f}")
    print(s.stats)
