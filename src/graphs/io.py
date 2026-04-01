import pandas as pd

def load_airports(path):
    df = pd.read_csv(path)
    return df

def load_edges(path):
    df = pd.read_csv(path)
    return df

def load_facebook_graph(path):
    graph = {}

    with open(path, "r") as f:
        for line in f:
            u, v = line.strip().split()

            if u not in graph:
                graph[u] = []
            if v not in graph:
                graph[v] = []

            graph[u].append((v, 1))
            graph[v].append((u, 1))

    return graph