import argparse
import time
from pathlib import Path

from graphs.graph import Graph, print_degree_sample_stats
from graphs.algorithms import bfs, dfs
from graphs.io import load_edge_csv_graph

DEFAULT_IMDB_DATASET = "data/dataset_parte2/imdb_edges.csv"
DEFAULT_CHECK_SOURCE = "tt0012313"


def _metricas_grafo(g2: Graph):
    """Retorna (|V|, |E| não-dir., grau médio, nó de maior grau, grau máximo)."""
    nodes = g2.get_nodes()
    if not nodes:
        return 0, 0, 0.0, None, 0
    n = len(nodes)
    total_deg = sum(len(g2.neighbors(v)) for v in nodes)
    e = total_deg // 2
    avg = total_deg / n
    max_node = max(nodes, key=lambda v: len(g2.neighbors(v)))
    max_deg = len(g2.neighbors(max_node))
    return n, e, avg, max_node, max_deg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=DEFAULT_IMDB_DATASET)
    parser.add_argument("--alg")
    parser.add_argument("--source")
    parser.add_argument("--weight-col", default="peso")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Ativa logs do loader e estatísticas de grau do grafo.",
    )

    args = parser.parse_args()

    if args.dataset:
        t0_total = time.time()
        dataset_path = Path(args.dataset).resolve()
        if dataset_path.suffix.lower() != ".csv":
            raise ValueError(
                "Use um CSV de arestas do IMDb (ex.: data/dataset_parte2/imdb_edges.csv)."
            )
        print(f"[cli] dataset: {dataset_path}")
        print(f"[cli] coluna de peso: {args.weight_col}")
        if args.alg:
            print(f"[cli] algoritmo: {args.alg}")

        dados = load_edge_csv_graph(
            str(dataset_path), weight_column=args.weight_col, debug=args.debug
        )

        g2 = Graph()
        seen_edges = set()
        for origem in dados:
            for destino, peso in dados[origem]:
                edge_key = tuple(sorted((origem, destino)))
                if edge_key in seen_edges:
                    continue
                seen_edges.add(edge_key)
                g2.add_edge(origem, destino, peso)

        if args.debug:
            print_degree_sample_stats(g2, sample_size=10)

        if args.alg == "CHECK":
            fonte = args.source or DEFAULT_CHECK_SOURCE
            n_v, n_e, grau_medio, no_max, grau_max = _metricas_grafo(g2)

            print("\n=== CHECK Parte 2 (resumo) ===")
            print(f"  |V| = {n_v}    |E| = {n_e}")
            print(f"  Grau médio: {grau_medio:.4f}")
            print(f"  Maior grau: {no_max} (grau {grau_max})")
            print(f"  Fonte BFS/DFS: {fonte}")

            t0_bfs = time.time()
            ordem_bfs, _ = bfs(g2, fonte)
            dt_bfs = time.time() - t0_bfs
            print(
                f"  BFS: visitados={len(ordem_bfs)}  "
                f"primeiros 5={ordem_bfs[:5]}  tempo={dt_bfs:.4f}s"
            )

            t0_dfs = time.time()
            ordem_dfs = dfs(g2, fonte)
            dt_dfs = time.time() - t0_dfs
            print(
                f"  DFS: visitados={len(ordem_dfs)}  "
                f"primeiros 5={ordem_dfs[:5]}  tempo={dt_dfs:.4f}s"
            )

            print(f"  Tempo total: {time.time() - t0_total:.4f}s")
            print("=== fim CHECK ===\n")

        elif args.alg == "BFS":
            inicio = time.time()
            resultado, niveis = bfs(g2, args.source)
            fim = time.time()

            print("BFS Parte 2 executado com sucesso")
            primeiros = resultado[:10]
            print("Primeiros 10 nós visitados e nível:")
            for n in primeiros:
                print(f"  {n}  (nível {niveis[n]})")
            print("Total visitados:", len(resultado))
            print("Tempo BFS:", fim - inicio)
            print("Tempo total (cli):", time.time() - t0_total)

        elif args.alg == "DFS":
            inicio = time.time()
            resultado = dfs(g2, args.source)
            fim = time.time()

            print("DFS Parte 2 executado com sucesso")
            print("Total visitados:", len(resultado))
            print("Tempo DFS:", fim - inicio)
            print("Tempo total (cli):", time.time() - t0_total)

if __name__ == "__main__":
    main()