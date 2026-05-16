import pandas as pd


def _colunas_vertices(df):
    if {"source", "target"}.issubset(df.columns):
        return "source", "target"
    if {"filme1", "filme2"}.issubset(df.columns):
        return "filme1", "filme2"
    raise ValueError("csv sem colunas de vertices: use source/target ou filme1/filme2")


def load_edge_csv_graph(path, weight_column="peso", debug=False, directed=False):
    df = pd.read_csv(path, dtype=str)
    source_col, target_col = _colunas_vertices(df)

    missing = {source_col, target_col} - set(df.columns)
    if missing:
        raise ValueError(f"csv sem colunas obrigatorias: {missing}")

    if weight_column not in df.columns:
        raise ValueError(f"coluna de peso inexistente: {weight_column}")

    graph = {}
    for _, row in df.iterrows():
        source = row[source_col]
        target = row[target_col]
        weight = float(row[weight_column])

        if source not in graph:
            graph[source] = []
        if target not in graph:
            graph[target] = []

        graph[source].append((target, weight))
        if not directed:
            graph[target].append((source, weight))

    if debug:
        n_nodes = len(graph)
        n_edges_undirected = sum(len(graph[n]) for n in graph) // 2
        print(f"[load_edge_csv_graph] arquivo: {path}")
        print(f"[load_edge_csv_graph] nos |V| = {n_nodes}")
        print(f"[load_edge_csv_graph] arestas |E| (nao-dir.) = {n_edges_undirected}")
        sample_nodes = sorted(graph.keys())[:5]
        for n in sample_nodes:
            viz = graph[n][:5]
            mais = len(graph[n]) - len(viz)
            sufixo = f" ... (+{mais} vizinhos)" if mais > 0 else ""
            print(f"  {n}: {viz}{sufixo}")

    return graph
