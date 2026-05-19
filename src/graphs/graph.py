import random


class Graph:
    def __init__(self):
        self.adj = {}

    def add_node(self, node):
        if node not in self.adj:
            self.adj[node] = {}

    def add_edge(self, u, v, weight=1.0):
        self.add_node(u)
        self.add_node(v)
        self.adj[u][v] = weight
        self.adj[v][u] = weight

    def add_directed_edge(self, u, v, weight=1.0):
        self.add_node(u)
        self.add_node(v)
        self.adj[u][v] = weight

    def neighbors(self, node):
        return self.adj.get(node, {}).items()

    def get_nodes(self):
        return list(self.adj.keys())

    def degree(self, node):
        return len(self.adj[node])

    def get_weight(self, u, v):
        return self.adj[u][v]

    def edges(self):
        edges = []
        for u in self.adj:
            for v, weight in self.adj[u].items():
                if u < v:
                    edges.append((u, v, weight))
        return edges

    def __len__(self):
        return len(self.adj)

    def __getitem__(self, node):
        return self.adj[node]

    def __contains__(self, node):
        return node in self.adj

    def __iter__(self):
        return iter(self.adj)


def print_degree_sample_stats(graph, sample_size=10):
    nodes = graph.get_nodes()
    if not nodes:
        print("[graus] grafo vazio")
        return

    k = min(sample_size, len(nodes))
    sample = random.sample(nodes, k=k)
    print(f"[graus] amostra aleatoria ({k} nos):")
    for n in sample:
        print(f"  {n}: grau {len(graph.neighbors(n))}")

    max_node = max(nodes, key=lambda n: len(graph.neighbors(n)))
    max_deg = len(graph.neighbors(max_node))
    avg = sum(len(graph.neighbors(n)) for n in nodes) / len(nodes)
    print(f"[graus] maior grau: no {max_node} (grau {max_deg})")
    print(f"[graus] grau medio: {avg:.4f}")
