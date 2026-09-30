"""Distributed asynchronous distance-vector routing (Chapter 5), Python version of rtinit/rtupdate.
Topology from the book: 0-1:1, 0-2:3, 0-3:7, 1-2:1, 2-3:2.   Run: python dv.py"""
import random
from collections import deque

INF = 999
LINKS = {(0, 1): 1, (0, 2): 3, (0, 3): 7, (1, 2): 1, (2, 3): 2}
N = 4
cost = {i: {} for i in range(N)}
for (a, b), c in LINKS.items():
    cost[a][b] = cost[b][a] = c

links = {}  # per-link FIFO queues of routing packets: (src,dst) -> deque of min_costs (links never reorder)

class Node:
    def __init__(self, i):
        self.i = i
        # dt[dest][via] = cost to reach dest by going through neighbour 'via'
        self.dt = [[INF] * N for _ in range(N)]
        for nb, c in cost[i].items():
            self.dt[nb][nb] = c
        self.dt[i][i] = 0
        self.notify()                                   # rtinit
    def mincosts(self):
        return [min(row) for row in self.dt]
    def notify(self):
        for nb in cost[self.i]:
            links.setdefault((self.i, nb), deque()).append(self.mincosts())
    def update(self, src, vec):                         # rtupdate
        before = self.mincosts()
        for d in range(N):
            if d != self.i:
                self.dt[d][src] = min(INF, cost[self.i][src] + vec[d])
        if self.mincosts() != before:
            self.notify()

nodes = [Node(i) for i in range(N)]
while any(links.values()):
    src, dst = random.choice([k for k, q in links.items() if q])   # random link = asynchrony
    nodes[dst].update(src, links[(src, dst)].popleft())              # FIFO within a link

for n in nodes:
    print(f"Node {n.i}: min costs {n.mincosts()}")
    for d in range(N):
        print(f"   to {d}: " + "  ".join(f"via {v}={n.dt[d][v] if n.dt[d][v] < INF else 'inf'}" for v in cost[n.i]))
