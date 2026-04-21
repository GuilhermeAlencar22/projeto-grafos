"""monta imdb_titles.csv com o nome dos filmes para os ids que aparecem nos csvs."""

from __future__ import annotations

import argparse
import csv
import gzip
from pathlib import Path

from imdb_titles import load_imdb_primary_title_map


def _ensure_gzip(path: Path) -> None:
    with open(path, "rb") as fh:
        magic = fh.read(2)
    if magic != b"\x1f\x8b":
        raise ValueError(
            f"Arquivo inválido para gzip: {path}. Esperado title.basics.tsv.gz do IMDb."
        )


def _projeto_root() -> Path:
    return Path(__file__).resolve().parents[2]


def collect_tconsts(paths: list[Path]) -> set[str]:
    ids: set[str] = set()
    for p in paths:
        if not p.exists():
            raise FileNotFoundError(p)
        with open(p, encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            if "source" not in reader.fieldnames or "target" not in reader.fieldnames:
                raise ValueError(f"{p}: colunas source e target obrigatórias")
            for row in reader:
                ids.add((row.get("source") or "").strip())
                ids.add((row.get("target") or "").strip())
    ids.discard("")
    return ids


def fetch_primary_titles_from_basics(
    basics_gz: Path, needed: set[str]
) -> dict[str, str]:
    _ensure_gzip(basics_gz)
    out: dict[str, str] = {}
    needed_tt = {x for x in needed if x.startswith("tt")}
    for x in needed:
        if x not in needed_tt:
            out[x] = ""
    if not needed_tt:
        return out

    remaining = set(needed_tt)
    with gzip.open(basics_gz, "rt", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            tc = (row.get("tconst") or "").strip()
            if tc not in remaining:
                continue
            title = row.get("primaryTitle") or ""
            if title == r"\N":
                title = ""
            out[tc] = title.strip()
            remaining.discard(tc)
            if not remaining:
                break
    for tc in remaining:
        out[tc] = ""
    return out


def write_imdb_titles_csv(output: Path, tconst_to_title: dict[str, str]) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(tconst_to_title.items(), key=lambda x: x[0])
    with open(output, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["tconst", "primaryTitle"])
        for tc, title in rows:
            w.writerow([tc, title])
    return len(rows)


def main() -> None:
    root = _projeto_root()
    parser = argparse.ArgumentParser(
        description="Extrai tconst + primaryTitle para IDs usados nos CSVs do dataset."
    )
    default_basics = root / "data/dataset_parte2/imdb/title.basics.tsv.gz"
    parser.add_argument(
        "--basics",
        default=str(default_basics),
        help=(
            "Caminho para title.basics.tsv.gz (somente neste script). "
            f"Padrão: {default_basics}"
        ),
    )
    parser.add_argument(
        "--edges",
        default=str(root / "data/dataset_parte2/imdb_edges.csv"),
        help="CSV de arestas (default: data/dataset_parte2/imdb_edges.csv)",
    )
    parser.add_argument(
        "--bellman",
        default=str(root / "data/dataset_parte2/imdb_bellman_ford.csv"),
        help="CSV Bellman-Ford (default: data/dataset_parte2/imdb_bellman_ford.csv)",
    )
    parser.add_argument(
        "--output",
        default=str(root / "data/dataset_parte2/imdb_titles.csv"),
        help="Saída (default: data/dataset_parte2/imdb_titles.csv)",
    )
    args = parser.parse_args()

    basics_path = Path(args.basics).resolve()
    edges_path = Path(args.edges).resolve()
    bellman_path = Path(args.bellman).resolve()
    output_path = Path(args.output).resolve()

    if not basics_path.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {basics_path}\n"
            "Baixe title.basics.tsv.gz do IMDb para essa pasta ou passe --basics CAMINHO."
        )

    needed = collect_tconsts([edges_path, bellman_path])
    print(f"IDs distintos (edges + bellman): {len(needed)}")

    print(f"Lendo {basics_path.name}...")
    found = fetch_primary_titles_from_basics(basics_path, needed)

    n = write_imdb_titles_csv(output_path, found)
    print(f"Linhas escritas em {output_path}: {n}")

    # le o csv de saida de novo (teste rapido)
    _ = load_imdb_primary_title_map(output_path)
    print("Helper load_imdb_primary_title_map: OK")


if __name__ == "__main__":
    main()
