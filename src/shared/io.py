"""leitura e validação de datasets CSV para construção dos grafos."""

import csv

import pandas as pd

from src.shared.graph import Graph


def carregar_aeroportos(path):
    aeroportos = {}
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            codigo = row.get("iata", "").strip()
            if not codigo:
                continue
            aeroportos[codigo] = {
                "cidade": row.get("cidade", "").strip(),
                "regiao": row.get("regiao", "").strip(),
            }
    return aeroportos


def carregar_grafo(path):
    grafo = Graph()
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            origem = row.get("origem", "").strip()
            destino = row.get("destino", "").strip()
            if not origem or not destino:
                continue
            try:
                peso = float(row.get("peso", 1.0))
            except (ValueError, TypeError):
                peso = 1.0
            grafo.add_edge(origem, destino, peso)
    return grafo


def _colunas_vertices(df):
    if {"origem", "destino"}.issubset(df.columns):
        return "origem", "destino"
    if {"source", "target"}.issubset(df.columns):
        return "source", "target"
    if {"filme1", "filme2"}.issubset(df.columns):
        return "filme1", "filme2"
    raise ValueError("csv sem colunas de vertices: use origem/destino ou filme1/filme2")


def load_edge_csv_graph(path, weight_column="peso", debug=False, directed=False):
    df = pd.read_csv(path, dtype=str)
    origem_col, destino_col = _colunas_vertices(df)

    if weight_column not in df.columns:
        raise ValueError(f"coluna de peso inexistente: {weight_column}")

    graph = {}
    for _, row in df.iterrows():
        origem = row[origem_col]
        destino = row[destino_col]
        weight = float(row[weight_column])

        graph.setdefault(origem, [])
        graph.setdefault(destino, [])
        graph[origem].append((destino, weight))
        if not directed:
            graph[destino].append((origem, weight))

    if debug:
        n_nodes = len(graph)
        n_edges_undirected = sum(len(graph[n]) for n in graph) // 2
        print(f"[load_edge_csv_graph] arquivo: {path}")
        print(f"[load_edge_csv_graph] nos |V| = {n_nodes}")
        print(f"[load_edge_csv_graph] arestas |E| (nao-dir.) = {n_edges_undirected}")
        for n in sorted(graph.keys())[:5]:
            viz = graph[n][:5]
            mais = len(graph[n]) - len(viz)
            sufixo = f" ... (+{mais} vizinhos)" if mais > 0 else ""
            print(f"  {n}: {viz}{sufixo}")

    return graph
