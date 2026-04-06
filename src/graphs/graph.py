class Graph:
    def __init__(self):
        self.adj = {}

    def add_node(self, node):
        if node not in self.adj:
            self.adj[node] = {}

    def add_edge(self, u, v, weight=1.0):
        self.add_node(u)
        self.add_node(v)
        if v not in self.adj[u]:
            self.adj[u][v] = weight
            self.adj[v][u] = weight

    def neighbors(self, node):
        return self.adj[node].items() 

    def get_nodes(self):
        return list(self.adj.keys())

    def degree(self, node):
        return len(self.adj[node])

    def get_weight(self, u, v):
        return self.adj[u][v]

    def edges(self):
        edges = []
        for u in self.adj:
            for v in self.adj[u]:
                if u < v:
                    edges.append((u, v, self.adj[u][v]))
        return edges

    def __len__(self):
        return len(self.adj)

    def __getitem__(self, node):
        return self.adj[node]

    def __contains__(self, node):
        return node in self.adj