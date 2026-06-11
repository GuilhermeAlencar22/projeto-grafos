"""executa os fluxos principais do projeto."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.parte2 import cli as cli_mod


def salvar_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def salvar_csv(path, data):
    if not data:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)


def rodar_parte1():
    from src.shared.algorithms import dijkstra
    from src.shared.io import carregar_aeroportos, carregar_grafo
    from src.parte1.metrics import (
        calcular_graus,
        ego_network_metrics,
        metricas_globais,
        subgrafo_por_regiao,
    )
    from src.viz import (
        gerar_arvore_percurso,
        gerar_grafo_interativo,
        plot_histograma_graus,
        plot_ranking,
        plot_regioes,
        plot_subgrafo_hubs,
    )

    os.makedirs("out", exist_ok=True)

    aeroportos = carregar_aeroportos("data/aeroportos_data.csv")
    grafo = carregar_grafo("data/adjacencias_aeroportos.csv")

    salvar_json("out/global.json", metricas_globais(grafo))
    salvar_json("out/regioes.json", subgrafo_por_regiao(grafo, aeroportos))

    ego = ego_network_metrics(grafo)
    salvar_csv("out/ego_aeroportos.csv", ego)

    graus = sorted(calcular_graus(grafo), key=lambda x: x["grau"], reverse=True)
    salvar_csv("out/graus.csv", graus)

    rankings = {
        "mais_conectado": graus[0] if graus else None,
        "maior_densidade_local": max(ego, key=lambda x: x["densidade_ego"])
        if ego
        else None,
    }
    salvar_json("out/rankings.json", rankings)

    rotas = []
    with open("data/rotas.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            origem = row.get("origem")
            destino = row.get("destino")
            if not origem or not destino:
                continue

            custo, caminho = dijkstra(grafo, origem, destino)
            rotas.append(
                {
                    "origem": origem,
                    "destino": destino,
                    "custo": round(custo, 2) if custo != float("inf") else custo,
                    "caminho": " -> ".join(caminho) if caminho else "sem caminho",
                }
            )

    salvar_csv("out/distancias_rotas.csv", rotas)

    def _caminho_de(origem, destino):
        for rota in rotas:
            if rota["origem"] == origem and rota["destino"] == destino and rota["caminho"] != "sem caminho":
                return [rota["caminho"].split(" -> ")]
        return []

    caminho_rec_poa = _caminho_de("REC", "POA")
    caminho_mao_gru = _caminho_de("MAO", "GRU")
    caminhos_obrigatorios = caminho_rec_poa + caminho_mao_gru

    if caminhos_obrigatorios:
        gerar_arvore_percurso(grafo, caminhos_obrigatorios, aeroportos, output_path="out/arvore_percurso.html")
    if caminho_mao_gru:
        gerar_arvore_percurso(grafo, caminho_mao_gru, aeroportos, output_path="out/arvore_percurso_gru_mao.html")
    plot_histograma_graus(grafo)
    plot_ranking(grafo)
    plot_regioes(grafo, aeroportos)
    plot_subgrafo_hubs(grafo, aeroportos)
    gerar_grafo_interativo(grafo, aeroportos, ego)


def rodar_parte2(args):
    if cli_mod.DEFAULT_REPORT_PATH.exists():
        cli_mod.DEFAULT_REPORT_PATH.unlink()

    algoritmos = ["CHECK", "BFS", "DFS"]
    if not args.rapido:
        algoritmos.extend(["TRES_FONTES", "DIJKSTRA", "BELLMAN_FORD"])

    base = argparse.Namespace(
        dataset=args.dataset,
        source=None,
        target=None,
        weight_col="peso",
        debug=args.debug,
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


def main():
    parser = argparse.ArgumentParser(description="executa parte1, parte2 ou tudo.")
    parser.add_argument(
        "parte",
        nargs="?",
        choices=["parte1", "parte2", "all"],
        default="all",
    )
    parser.add_argument(
        "--dataset",
        default=str(ROOT / "data" / "dataset_parte2" / "Imdb_arestas.csv"),
        help="csv usado na parte 2.",
    )
    parser.add_argument(
        "--rapido",
        action="store_true",
        help="na parte 2, roda so check, bfs e dfs.",
    )
    parser.add_argument("--debug", action="store_true", help="logs extras.")
    args = parser.parse_args()

    if args.parte in {"parte1", "all"}:
        print("\n[solve] === PARTE 1 ===\n")
        rodar_parte1()

    if args.parte in {"parte2", "all"}:
        print("\n[solve] === PARTE 2 ===\n")
        rodar_parte2(args)


if __name__ == "__main__":
    main()
