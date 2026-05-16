"""gera o grafo completo usado pela interface.

usado pela interface para:
- modo 'grafo completo' (renderizacao pesada, opcional);
- roteamento film x film no dataset real.

uso:
    python -m src.parte2.build_interface_grafo
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def build_grafo(filmes_path: Path, arestas_path: Path) -> dict:
    filmes: dict[str, dict] = {}
    with filmes_path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            nome = (row.get("filme") or "").strip()
            if not nome:
                continue
            filmes[nome] = {
                "titulo": nome,
                "ano": (row.get("ano") or "").strip(),
                "generos": (row.get("generos") or "").strip(),
                "nota": (row.get("nota") or "").strip(),
            }

    arestas: list[dict] = []
    with arestas_path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            s = (row.get("filme1") or "").strip()
            t = (row.get("filme2") or "").strip()
            if not s or not t:
                continue
            try:
                sim = float(row.get("similaridade") or 0)
                peso = float(row.get("peso") or 0)
                atores = int(float(row.get("qtd_atores_compartilhados") or 0))
            except ValueError:
                continue
            arestas.append({
                "origem": s,
                "destino": t,
                "sim": int(sim) if sim == int(sim) else round(sim, 4),
                "p": round(peso, 6),
                "a": atores,
            })

    posicoes = _computar_layout(arestas)

    return {
        "meta": {
            "descricao": "grafo completo da parte 2 - todas as arestas do csv",
            "filmes_total": len(filmes),
            "arestas_total": len(arestas),
            "aviso": "posicoes pre-computadas por grau; o browser so pinta, sem calcular layout",
        },
        "filmes": filmes,
        "arestas": arestas,
        "posicoes": posicoes,
    }


def _computar_layout(arestas: list[dict]) -> dict[str, dict]:
    """posiciona hubs perto do centro e perifericos nos aneis externos."""
    grau: dict[str, int] = {}
    for e in arestas:
        grau[e["origem"]] = grau.get(e["origem"], 0) + 1
        grau[e["destino"]] = grau.get(e["destino"], 0) + 1

    nos_ordenados = sorted(grau.keys(), key=lambda n: grau[n], reverse=True)
    n = len(nos_ordenados)

    aneis = [
        (0.01, 300),
        (0.05, 900),
        (0.15, 1800),
        (0.35, 3000),
        (0.65, 4500),
        (1.00, 6500),
    ]

    posicoes: dict[str, dict] = {}
    idx_inicio = 0

    for fracao, raio in aneis:
        idx_fim = max(idx_inicio + 1, int(n * fracao))
        nos_anel = nos_ordenados[idx_inicio:idx_fim]
        qtd = len(nos_anel)

        for i, nome in enumerate(nos_anel):
            angulo = (2 * math.pi * i) / qtd
            posicoes[nome] = {
                "x": round(raio * math.cos(angulo), 1),
                "y": round(raio * math.sin(angulo), 1),
            }

        idx_inicio = idx_fim

    return posicoes


def main() -> None:
    root = _root()
    parser = argparse.ArgumentParser(
        description="gera parte2_grafo.json com todas as arestas."
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
        "--out",
        type=Path,
        default=root / "interface/data/parte2_grafo.json",
    )
    args = parser.parse_args()

    print("[grafo] lendo csvs...")
    grafo = build_grafo(args.filmes, args.arestas)
    print(f"[grafo] {grafo['meta']['filmes_total']} filmes, {grafo['meta']['arestas_total']} arestas")
    _write_json(args.out, grafo)

    tamanho_mb = args.out.stat().st_size / 1_048_576
    print(f"[grafo] -> {args.out}  ({tamanho_mb:.1f} MB)")


if __name__ == "__main__":
    main()
