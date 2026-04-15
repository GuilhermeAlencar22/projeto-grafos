import pandas as pd

def load_airports(path):
    df = pd.read_csv(path)
    return df

def load_edges(path):
    df = pd.read_csv(path)
    return df

def load_facebook_teste_graph(path):
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


def load_edge_csv_graph(path, weight_column="peso"):
    df = pd.read_csv(path, dtype={"source": str, "target": str})

    required_columns = {"source", "target"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"CSV sem colunas obrigatorias: {missing}")

    if weight_column not in df.columns:
        raise ValueError(f"Coluna de peso inexistente: {weight_column}")

    graph = {}
    for _, row in df.iterrows():
        source = row["source"]
        target = row["target"]
        weight = float(row[weight_column])

        if source not in graph:
            graph[source] = []
        if target not in graph:
            graph[target] = []

        graph[source].append((target, weight))
        graph[target].append((source, weight))

    return graph