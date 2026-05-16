"""gera a amostra leve usada pela interface.

uso:
    python -m src.parte2.build_interface_amostra
    python -m src.parte2.build_interface_amostra --filmes ... --arestas ... --report ...
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict, deque
from pathlib import Path


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


def _split_pipe(value: str) -> list[str]:
    return [item.strip() for item in str(value or "").split("|") if item.strip()]


def load_movies(path: Path) -> dict[str, dict]:
    movies: dict[str, dict] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            name = (row.get("filme") or "").strip()
            if not name:
                continue
            movies[name] = {
                "titulo": name,
                "ano": (row.get("ano") or "").strip(),
                "generos": (row.get("generos") or "").strip(),
                "nota": (row.get("nota") or "").strip(),
                "diretores": (row.get("diretores") or "").strip(),
            }
    return movies


def load_edges(path: Path) -> list[dict]:
    edges: list[dict] = []
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            origem = (row.get("filme1") or "").strip()
            destino = (row.get("filme2") or "").strip()
            if not origem or not destino:
                continue
            actors = int(float(row.get("qtd_atores_compartilhados") or 0))
            similarity = float(row.get("similaridade") or 0)
            weight = float(row.get("peso") or 0)
            edge = {
                "origem": origem,
                "destino": destino,
                "actors_common": actors,
                "actors_common_names": _split_pipe(row.get("atores_compartilhados") or ""),
                "generos_compartilhados": _split_pipe(row.get("generos_compartilhados") or ""),
                "similaridade": int(similarity) if similarity.is_integer() else similarity,
                "peso": weight,
            }
            edge["id"] = edge_key(origem, destino)
            edges.append(edge)
    return edges


def edge_key(a: str, b: str) -> str:
    return "|".join(sorted([a, b]))


def build_adj(edges: list[dict]) -> dict[str, list[dict]]:
    adj: dict[str, list[dict]] = defaultdict(list)
    for edge in edges:
        adj[edge["origem"]].append(edge)
        adj[edge["destino"]].append(edge)
    return adj


def _other(edge: dict, node: str) -> str:
    return edge["destino"] if edge["origem"] == node else edge["origem"]


def _connected_sample(seed_edges: list[dict], limit: int) -> list[dict]:
    if not seed_edges:
        return []
    selected = [seed_edges[0]]
    used = {seed_edges[0]["id"]}
    nodes = {seed_edges[0]["origem"], seed_edges[0]["destino"]}
    while len(selected) < limit:
        nxt = next(
            (
                edge
                for edge in seed_edges
                if edge["id"] not in used
                and (edge["origem"] in nodes or edge["destino"] in nodes)
            ),
            None,
        )
        if nxt is None:
            break
        selected.append(nxt)
        used.add(nxt["id"])
        nodes.add(nxt["origem"])
        nodes.add(nxt["destino"])
    return selected


def _edges_from_paths(report: dict, edge_map: dict[str, dict]) -> list[dict]:
    selected: list[dict] = []
    seen: set[str] = set()
    for item in report.get("dijkstra") or []:
        path = item.get("caminho") or []
        for a, b in zip(path, path[1:]):
            key = edge_key(a, b)
            edge = edge_map.get(key)
            if edge and key not in seen:
                selected.append(edge)
                seen.add(key)
    return selected


def _traversal_edges(
    fontes: list[str], adj: dict[str, list[dict]], limit_each: int
) -> list[dict]:
    selected: list[dict] = []
    seen: set[str] = set()
    for origem in fontes:
        if origem not in adj:
            continue
        queue = deque([origem])
        visited = {origem}
        while queue and len([e for e in selected if origem in e["id"]]) < limit_each:
            node = queue.popleft()
            for edge in sorted(
                adj[node],
                key=lambda e: (e["similaridade"], e["actors_common"]),
                reverse=True,
            ):
                key = edge["id"]
                if key not in seen:
                    selected.append(edge)
                    seen.add(key)
                nxt = _other(edge, node)
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)
                if len(seen) >= limit_each * max(1, len(fontes)):
                    break
    return selected


def build_amostra(movies: dict[str, dict], edges: list[dict], report: dict) -> dict:
    """monta a amostra visual sem carregar o csv inteiro no navegador."""
    edge_map = {edge["id"]: edge for edge in edges}
    adj = build_adj(edges)
    degree: Counter = Counter()
    for edge in edges:
        degree[edge["origem"]] += 1
        degree[edge["destino"]] += 1

    by_similarity = sorted(
        edges,
        key=lambda e: (e["similaridade"], e["actors_common"]),
        reverse=True,
    )

    top_nodes = {name for name, _ in degree.most_common(36)}
    top_connection_edges = [
        edge for edge in edges if edge["origem"] in top_nodes or edge["destino"] in top_nodes
    ]
    top_connection_edges.sort(
        key=lambda e: (
            degree[e["origem"]] + degree[e["destino"]],
            e["actors_common"],
            e["similaridade"],
        ),
        reverse=True,
    )

    tres_fontes = report.get("tres_fontes") or {}
    fontes = list(tres_fontes.get("fontes_utilizadas") or tres_fontes.get("fontes") or [])
    if not fontes:
        fontes = ["Jurassic Park", "Forrest Gump", "Pulp Fiction"]

    selected: list[dict] = []
    selected.extend(_connected_sample(by_similarity, 80))
    selected.extend(top_connection_edges[:140])
    selected.extend(_edges_from_paths(report, edge_map))
    selected.extend(_traversal_edges(fontes, adj, 36))

    edge_out: dict[str, dict] = {}
    movie_names: set[str] = set()
    for edge in selected:
        edge_out[edge["id"]] = edge
        movie_names.add(edge["origem"])
        movie_names.add(edge["destino"])

    for item in report.get("dijkstra") or []:
        movie_names.add(item.get("origem", ""))
        movie_names.add(item.get("destino", ""))
        movie_names.update(item.get("caminho") or [])
    movie_names.update(fontes)

    return {
        "meta": {
            "descricao": "amostra leve do grafo para a interface da parte 2",
            "fonte_filmes": "data/dataset_parte2/Imdb_filmes.csv",
            "fonte_arestas": "data/dataset_parte2/Imdb_arestas.csv",
            "movies_total": len(movies),
            "edges_total": len(edge_out),
            "observacao": "todos os filmes do csv estao em movies; edges e amostra visual para nao travar o navegador.",
        },
        "movies": {
            name: movies[name]
            for name in sorted(movies)
            if name
        },
        "edges": dict(sorted(edge_out.items())),
    }


def main() -> None:
    root = _root()
    parser = argparse.ArgumentParser(
        description="gera parte2_amostra.json para a interface."
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
        "--out",
        type=Path,
        default=root / "interface/data/parte2_amostra.json",
    )
    args = parser.parse_args()

    movies = load_movies(args.filmes)
    edges = load_edges(args.arestas)
    report = _read_json(args.report)

    amostra = build_amostra(movies, edges, report)
    _write_json(args.out, amostra)

    print(f"amostra -> {args.out}")
    print(f"amostra: {len(amostra['movies'])} filmes, {len(amostra['edges'])} arestas")


if __name__ == "__main__":
    main()

