import argparse
import json
import time
from collections import Counter
from pathlib import Path

from graphs.graph import Graph, print_degree_sample_stats
from graphs.algorithms import bfs, dfs
from graphs.io import load_edge_csv_graph

DEFAULT_IMDB_DATASET = "data/dataset_parte2/imdb_edges.csv"
DEFAULT_CHECK_SOURCE = "tt0012313"
DEFAULT_REPORT_PATH = Path(__file__).resolve().parents[1] / "out" / "parte2_report.json"


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


def _metricas_componentes(g2: Graph):
    """Retorna (quantidade_componentes, tamanho_maior_componente)."""
    visited = set()
    componentes = 0
    maior = 0

    for start in g2.get_nodes():
        if start in visited:
            continue

        componentes += 1
        stack = [start]
        tamanho = 0
        visited.add(start)

        while stack:
            node = stack.pop()
            tamanho += 1
            for vizinho, _ in g2.neighbors(node):
                if vizinho not in visited:
                    visited.add(vizinho)
                    stack.append(vizinho)

        maior = max(maior, tamanho)

    return componentes, maior


def _distribuicao_graus(g2: Graph):
    """Retorna distribuição organizada de graus (grau -> quantidade de nós)."""
    counter = Counter(len(g2.neighbors(n)) for n in g2.get_nodes())
    return {str(grau): qtd for grau, qtd in sorted(counter.items())}


def _sanear_estrutura_report(report: dict) -> None:
    """Remove legado 'bfs_dfs', garante listas 'bfs' e 'dfs' sem apagar dados atuais."""
    report.pop("bfs_dfs", None)
    report.setdefault("bfs", [])
    report.setdefault("dfs", [])


def _atualizar_report_dataset(report_path: Path, dataset_info: dict):
    """Atualiza somente a chave 'dataset', preservando bfs/dfs e demais chaves."""
    if report_path.exists():
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            report = {}
    else:
        report = {}

    _sanear_estrutura_report(report)
    report["dataset"] = dataset_info
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _registrar_execucao_busca(
    report_path: Path,
    algoritmo: str,
    source: str,
    tempo: float,
    *,
    visitados: int | None = None,
    primeiros_nos: list | None = None,
    tempo_total_cli: float | None = None,
):
    """Registra execução de BFS/DFS em listas separadas; não altera o bloco dataset."""
    if report_path.exists():
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            report = {}
    else:
        report = {}

    _sanear_estrutura_report(report)
    chave = algoritmo.lower()
    if chave not in ("bfs", "dfs"):
        raise ValueError(f"Algoritmo invalido para registro no report: {algoritmo}")

    entrada: dict = {
        "source": str(source),
        "tempo": round(float(tempo), 9),
    }
    if visitados is not None:
        entrada["visitados"] = visitados
    if primeiros_nos is not None:
        entrada["primeiros_nos"] = primeiros_nos
    if tempo_total_cli is not None:
        entrada["tempo_total_cli"] = round(float(tempo_total_cli), 9)

    report[chave].append(entrada)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


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
            graus = [len(g2.neighbors(n)) for n in g2.get_nodes()]
            grau_min = min(graus) if graus else 0
            grau_maximo = max(graus) if graus else 0
            qtd_componentes, maior_componente = _metricas_componentes(g2)
            distribuicao = _distribuicao_graus(g2)

            dataset_info = {
                "nome": dataset_path.name,
                "|V|": n_v,
                "|E|": n_e,
                "tipo": "nao-direcionado",
                "ponderado": True,
                "grau": {
                    "min": grau_min,
                    "max": grau_maximo,
                    "medio": round(grau_medio, 6),
                },
                "componentes_conexas": qtd_componentes,
                "maior_componente_conexa": maior_componente,
                "distribuicao_graus": distribuicao,
            }
            _atualizar_report_dataset(DEFAULT_REPORT_PATH, dataset_info)

            print("\n=== CHECK Parte 2 (resumo) ===")
            print(f"  |V| = {n_v}    |E| = {n_e}")
            print(f"  Grau médio: {grau_medio:.4f}")
            print(f"  Maior grau: {no_max} (grau {grau_max})")
            print(f"  Componentes conexas: {qtd_componentes}")
            print(f"  Maior componente: {maior_componente}")
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
            print(f"  Report dataset atualizado em: {DEFAULT_REPORT_PATH}")
            print("=== fim CHECK ===\n")

        elif args.alg == "BFS":
            fonte_exec = args.source or DEFAULT_CHECK_SOURCE
            inicio = time.time()
            resultado, niveis = bfs(g2, fonte_exec)
            fim = time.time()
            tempo_bfs = fim - inicio

            print("BFS Parte 2 executado com sucesso")
            primeiros = resultado[:10]
            print("Primeiros 10 nós visitados e nível:")
            for n in primeiros:
                print(f"  {n}  (nível {niveis[n]})")
            print("Total visitados:", len(resultado))
            print("Tempo BFS:", tempo_bfs)
            tempo_cli = time.time() - t0_total
            print("Tempo total (cli):", tempo_cli)
            _registrar_execucao_busca(
                DEFAULT_REPORT_PATH,
                "bfs",
                fonte_exec,
                tempo_bfs,
                visitados=len(resultado),
                primeiros_nos=resultado[:10],
                tempo_total_cli=tempo_cli,
            )
            print(f"Execução registrada em: {DEFAULT_REPORT_PATH}")

        elif args.alg == "DFS":
            fonte_exec = args.source or DEFAULT_CHECK_SOURCE
            inicio = time.time()
            resultado = dfs(g2, fonte_exec)
            fim = time.time()
            tempo_dfs = fim - inicio

            print("DFS Parte 2 executado com sucesso")
            print("Total visitados:", len(resultado))
            print("Tempo DFS:", tempo_dfs)
            tempo_cli = time.time() - t0_total
            print("Tempo total (cli):", tempo_cli)
            _registrar_execucao_busca(
                DEFAULT_REPORT_PATH,
                "dfs",
                fonte_exec,
                tempo_dfs,
                visitados=len(resultado),
                primeiros_nos=resultado[:10],
                tempo_total_cli=tempo_cli,
            )
            print(f"Execução registrada em: {DEFAULT_REPORT_PATH}")

if __name__ == "__main__":
    main()