import random


class Graph:
    def __init__(self):
        self.adj = {}

    def add_node(self, node):
        if node not in self.adj:
            self.adj[node] = []

    def add_edge(self, u, v, weight=1):
        self.add_node(u)
        self.add_node(v)

        self.adj[u].append((v, weight))
        self.adj[v].append((u, weight))

    def add_directed_edge(self, u, v, weight=1):
        self.add_node(u)
        self.add_node(v)
        self.adj[u].append((v, weight))

    def neighbors(self, node):
        if node in self.adj:
            return self.adj[node]
        return []

    def get_nodes(self):
        return list(self.adj.keys())

    def show_graph(self):
        for node in self.adj:
            print(node, "->", self.adj[node])


def print_degree_sample_stats(graph, sample_size=10):
    nodes = graph.get_nodes()
    if not nodes:
        print("[graus] grafo vazio")
        return

    k = min(sample_size, len(nodes))
    sample = random.sample(nodes, k=k)
    print(f"[graus] amostra aleatória ({k} nós):")
    for n in sample:
        d = len(graph.neighbors(n))
        print(f"  {n}: grau {d}")

    max_node = max(nodes, key=lambda n: len(graph.neighbors(n)))
    max_deg = len(graph.neighbors(max_node))
    avg = sum(len(graph.neighbors(n)) for n in nodes) / len(nodes)
    print(f"[graus] maior grau: nó {max_node} (grau {max_deg})")
    print(f"[graus] grau médio: {avg:.4f}")