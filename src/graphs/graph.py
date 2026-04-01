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

    def neighbors(self, node):
        if node in self.adj:
            return self.adj[node]
        return []

    def get_nodes(self):
        return list(self.adj.keys())

    def show_graph(self):
        for node in self.adj:
            print(node, "->", self.adj[node])