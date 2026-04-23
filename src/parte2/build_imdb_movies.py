"""gera imdb_movies.csv so com tconst que aparecem em imdb_edges.csv (metadados leves)."""

from __future__ import annotations

import argparse
import csv
import gzip
from collections import defaultdict
from pathlib import Path

import pandas as pd


def _projeto_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _norm(s: str | None) -> str:
    if not s or s == r"\N":
        return ""
    return str(s).strip()


def tconsts_do_edges(edges_path: Path) -> set[str]:
    df = pd.read_csv(edges_path, usecols=["source", "target"], dtype=str)
    ids: set[str] = set()
    for c in ("source", "target"):
        ids.update(df[c].dropna().astype(str).str.strip())
    ids.discard("")
    return ids


def ler_basics(basics_path: Path, needed: set[str]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    with gzip.open(basics_path, "rt", encoding="utf-8", errors="replace", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            tc = _norm(row.get("tconst"))
            if not tc or tc not in needed:
                continue
            out[tc] = {
                "titulo": _norm(row.get("primaryTitle")),
                "ano": _norm(row.get("startYear")),
                "generos": _norm(row.get("genres")),
            }
    return out


def ler_ratings(ratings_path: Path, needed: set[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    with gzip.open(ratings_path, "rt", encoding="utf-8", errors="replace", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            tc = _norm(row.get("tconst"))
            if not tc or tc not in needed:
                continue
            out[tc] = _norm(row.get("averageRating"))
    return out


def ler_diretores(principals_path: Path, needed: set[str]) -> dict[str, list[str]]:
    por_titulo: dict[str, set[str]] = defaultdict(set)
    with gzip.open(principals_path, "rt", encoding="utf-8", errors="replace", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            if _norm(row.get("category")) != "director":
                continue
            tc = _norm(row.get("tconst"))
            if not tc or tc not in needed:
                continue
            nc = _norm(row.get("nconst"))
            if nc:
                por_titulo[tc].add(nc)
    return {tc: sorted(v) for tc, v in por_titulo.items()}


def ler_nomes_nconst(names_path: Path, nconsts: set[str]) -> dict[str, str]:
    """nconst -> primaryName (só entradas pedidas)."""
    if not nconsts:
        return {}
    out: dict[str, str] = {}
    faltam = len(nconsts)
    with gzip.open(names_path, "rt", encoding="utf-8", errors="replace", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            nc = _norm(row.get("nconst"))
            if not nc or nc not in nconsts or nc in out:
                continue
            nome = _norm(row.get("primaryName"))
            if nome:
                out[nc] = nome
            else:
                out[nc] = nc
            faltam -= 1
            if faltam <= 0:
                break
    return out


def main() -> None:
    root = _projeto_root()
    parser = argparse.ArgumentParser(
        description="imdb_movies.csv a partir de imdb_edges + tsv.gz locais (nao versionados)."
    )
    parser.add_argument(
        "--edges",
        type=Path,
        default=root / "data/dataset_parte2/imdb_edges.csv",
        help="csv de arestas (default: data/dataset_parte2/imdb_edges.csv)",
    )
    parser.add_argument(
        "--basics",
        type=Path,
        default=root / "data/dataset_parte2/imdb/title.basics.tsv.gz",
        help="title.basics.tsv.gz",
    )
    parser.add_argument(
        "--ratings",
        type=Path,
        default=root / "data/dataset_parte2/imdb/title.ratings.tsv.gz",
        help="title.ratings.tsv.gz",
    )
    parser.add_argument(
        "--principals",
        type=Path,
        default=root / "data/dataset_parte2/imdb/title.principals.tsv.gz",
        help="title.principals.tsv.gz",
    )
    parser.add_argument(
        "--names",
        type=Path,
        default=root / "data/dataset_parte2/imdb/name.basics.tsv.gz",
        help="name.basics.tsv.gz (opcional; se ausente, diretores = nconst)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "data/dataset_parte2/imdb_movies.csv",
        help="saida (default: data/dataset_parte2/imdb_movies.csv)",
    )
    args = parser.parse_args()

    for p in (args.edges, args.basics, args.ratings, args.principals):
        if not p.exists():
            raise FileNotFoundError(p)

    needed = tconsts_do_edges(args.edges)
    if not needed:
        raise ValueError("nenhum tconst em imdb_edges")

    print(f"tconst unicos no grafo: {len(needed)}")
    print("lendo basics...")
    basics = ler_basics(args.basics, needed)
    print(f"  encontrados: {len(basics)}")
    print("lendo ratings...")
    ratings = ler_ratings(args.ratings, needed)
    print(f"  com nota: {len(ratings)}")
    print("lendo diretores (principals)...")
    diretores = ler_diretores(args.principals, needed)
    print(f"  com director: {len(diretores)}")

    nconst_diretores: set[str] = set()
    for lst in diretores.values():
        nconst_diretores.update(lst)

    nome_por_nconst: dict[str, str] = {}
    if args.names.exists():
        print("lendo nomes (name.basics)...")
        nome_por_nconst = ler_nomes_nconst(args.names, nconst_diretores)
        print(f"  nconst com nome: {len(nome_por_nconst)} de {len(nconst_diretores)}")
    else:
        print("name.basics ausente; diretores como nconst")

    def diretores_celula(nconsts: list[str]) -> str:
        partes = [nome_por_nconst.get(nc, nc) for nc in nconsts]
        return "|".join(partes)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["tconst", "titulo", "ano", "generos", "nota", "diretores"])
        for tc in sorted(needed):
            b = basics.get(tc, {})
            dirs = diretores.get(tc, [])
            w.writerow(
                [
                    tc,
                    b.get("titulo", ""),
                    b.get("ano", ""),
                    b.get("generos", ""),
                    ratings.get(tc, ""),
                    diretores_celula(dirs),
                ]
            )

    print(f"gravado: {args.output}")


if __name__ == "__main__":
    main()
