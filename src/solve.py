"""roda os 4 algoritmos da parte 2 em sequencia e gera out/parte2_report.json.

uso: python -m src.solve
"""

from __future__ import annotations

import argparse
from pathlib import Path

from src import cli as cli_mod

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="roda algs parte 2 no csv padrao; saida out/parte2_report.json."
    )
    parser.add_argument(
        "--dataset",
        default=str(ROOT / "data" / "dataset_parte2" / "Imdb_arestas.csv"),
        help="csv imdb nao-dirigido (check, bfs, dfs, etc.).",
    )
    parser.add_argument(
        "--rapido",
        action="store_true",
        help="so check, bfs e dfs (sem tres_fontes, dijkstra nem bellman_ford).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="repassa debug pro cli.",
    )
    args_cli = parser.parse_args()

    if cli_mod.DEFAULT_REPORT_PATH.exists():
        cli_mod.DEFAULT_REPORT_PATH.unlink()

    algoritmos = ["CHECK", "BFS", "DFS"]
    if not args_cli.rapido:
        algoritmos.extend(["TRES_FONTES", "DIJKSTRA", "BELLMAN_FORD"])

    base = argparse.Namespace(
        dataset=args_cli.dataset,
        source=None,
        weight_col="peso",
        debug=args_cli.debug,
        tres_fontes=cli_mod.DEFAULT_TRES_FONTES,
        dijkstra_pares=None,
        bellman_demo=False,
    )

    for nome_alg in algoritmos:
        run_args = argparse.Namespace(**vars(base))
        run_args.alg = nome_alg
        print(f"\n[solve] === {nome_alg} ===\n")
        cli_mod.executar_cli(run_args, ROOT)

    print(f"\n[solve] report: {cli_mod.DEFAULT_REPORT_PATH}\n")


if __name__ == "__main__":
    main()
