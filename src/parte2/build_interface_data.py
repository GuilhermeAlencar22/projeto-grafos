"""gera os jsons usados pela interface.

gera:
    interface/data/resumo_parte2.json
    interface/data/parte2_amostra.json

parte2_grafo.json e gerado separadamente:
    python -m src.parte2.build_interface_grafo

uso:
    python -m src.parte2.build_interface_data
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.parte2.build_interface_amostra import (
    build_amostra,
    load_edges,
    load_movies,
)


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _nomes_em_portugues(valor):
    if isinstance(valor, list):
        return [_nomes_em_portugues(item) for item in valor]
    if not isinstance(valor, dict):
        return valor

    nomes = {"ciclo": "tem_ciclo"}
    novo = {}
    for chave, item in valor.items():
        novo[nomes.get(chave, chave)] = _nomes_em_portugues(item)
    return novo


def build_resumo(report: dict) -> dict:
    """monta o resumo leve da parte 2 para consumo da interface."""
    tres = report.get("tres_fontes") or {}
    fontes = list(tres.get("fontes_utilizadas") or tres.get("fontes") or [])
    buscas = {
        "fontes_principais": fontes,
        "bfs": [],
        "dfs": [],
    }
    for bloco in tres.get("por_fonte") or []:
        origem = bloco.get("origem")
        for alg in ("bfs", "dfs"):
            item = dict(bloco.get(alg) or {})
            if item:
                item["origem"] = origem
                buscas[alg].append(item)

    if not buscas["bfs"]:
        buscas["bfs"] = list(report.get("bfs") or [])
    if not buscas["dfs"]:
        buscas["dfs"] = list(report.get("dfs") or [])

    resumo = {
        "meta": {
            "origem": "out/parte2_report.json",
            "descricao": "resumo preparado para consumo da interface da parte 2",
            "fontes_csv": [
                "data/dataset_parte2/Imdb_filmes.csv",
                "data/dataset_parte2/Imdb_arestas.csv",
            ],
        },
        "dataset": report.get("dataset") or {},
        "buscas": buscas,
        "dijkstra": list(report.get("dijkstra") or []),
        "bellman_ford": list(report.get("bellman_ford") or []),
        "benchmark": report.get("benchmark") or {},
        "visualizacoes": [
            {
                "titulo": "Benchmark de tempos",
                "arquivo": "assets/parte2_benchmark_tempos.png",
                "tipo": "comparacao_algoritmos",
            },
            {
                "titulo": "Distribuicao de graus",
                "arquivo": "assets/parte2_distribuicao_graus.png",
                "tipo": "estrutura_grafo",
            },
            {
                "titulo": "Componentes conexas",
                "arquivo": "assets/parte2_componentes_conexas.png",
                "tipo": "estrutura_grafo",
            },
            {
                "titulo": "Similaridade vs peso",
                "arquivo": "assets/parte2_similaridade_vs_peso.png",
                "tipo": "pesos",
            },
            {
                "titulo": "Atores em comum vs similaridade",
                "arquivo": "assets/parte2_atores_vs_similaridade.png",
                "tipo": "dataset",
            },
        ],
    }
    return _nomes_em_portugues(resumo)


def main() -> None:
    root = _root()
    parser = argparse.ArgumentParser(
        description="gera dados leves da interface a partir dos csvs finais."
    )
    parser.add_argument(
        "--filmes",
        type=Path,
        default=root / "data/dataset_parte2/Imdb_filmes.csv",
    )
    parser.add_argument(
        "--arestas",
        type=Path,
        default=root / "data/dataset_parte2/Imdb_arestas.csv",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=root / "out/parte2_report.json",
    )
    parser.add_argument(
        "--interface-data",
        type=Path,
        default=root / "interface/data",
    )
    args = parser.parse_args()

    movies = load_movies(args.filmes)
    edges = load_edges(args.arestas)
    report = _read_json(args.report)

    resumo = build_resumo(report)
    amostra = build_amostra(movies, edges, report)

    _write_json(args.interface_data / "resumo_parte2.json", resumo)
    _write_json(args.interface_data / "parte2_amostra.json", amostra)

    print(f"resumo -> {args.interface_data / 'resumo_parte2.json'}")
    print(f"amostra -> {args.interface_data / 'parte2_amostra.json'}")
    print(f"amostra: {len(amostra['movies'])} filmes, {len(amostra['edges'])} arestas")


if __name__ == "__main__":
    main()
