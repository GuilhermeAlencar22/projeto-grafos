import argparse
import time
from pathlib import Path

from graphs.graph import Graph
from graphs.algorithms import bfs, dfs
from graphs.io import load_facebook_teste_graph, load_edge_csv_graph

def main():
    g = Graph()

    # exemplo simples
    g.add_edge("REC", "SSA", 1)
    g.add_edge("REC", "GRU", 2)

    print("BFS:", bfs(g, "REC"))
    print("DFS:", dfs(g, "REC"))

    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset")
    parser.add_argument("--alg")
    parser.add_argument("--source")
    parser.add_argument("--weight-col", default="peso")

    args = parser.parse_args()

    if args.dataset and "dataset_parte2" in args.dataset:
        dataset_path = Path(args.dataset)
        if dataset_path.suffix.lower() == ".csv":
            dados = load_edge_csv_graph(args.dataset, weight_column=args.weight_col)
        else:
            dados = load_facebook_teste_graph(args.dataset)

        g2 = Graph()

        for origem in dados:
            for destino, peso in dados[origem]:
                g2.add_edge(origem, destino, peso)

        if args.alg == "BFS":
            inicio = time.time()
            resultado = bfs(g2, args.source)
            fim = time.time()

            print("BFS Parte 2 executado com sucesso")
            print("Total visitados:", len(resultado))
            print("Tempo:", fim - inicio)

        elif args.alg == "DFS":
            inicio = time.time()
            resultado = dfs(g2, args.source)
            fim = time.time()

            print("DFS Parte 2 executado com sucesso")
            print("Total visitados:", len(resultado))
            print("Tempo:", fim - inicio)

if __name__ == "__main__":
    main()