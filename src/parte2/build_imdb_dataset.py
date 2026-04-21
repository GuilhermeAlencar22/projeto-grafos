"""monta imdb_edges.csv cruzando elenco, genero e notas dos arquivos do imdb."""

import argparse
import csv
import gzip
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import pandas as pd


VALID_TITLE_TYPES = {"movie", "tvMovie"}
VALID_ACTOR_CATEGORIES = {"actor", "actress", "self"}


def _ensure_gzip(path: Path) -> None:
    with open(path, "rb") as fh:
        magic = fh.read(2)
    if magic != b"\x1f\x8b":
        raise ValueError(
            f"Arquivo invalido para gzip: {path}. "
            "Baixe novamente do IMDb e substitua o arquivo."
        )


def load_titles(path: Path, max_titles: int | None = None) -> dict[str, set[str]]:
    _ensure_gzip(path)
    df = pd.read_csv(path, sep="\t", compression="gzip", dtype=str, na_filter=False)
    df = df[df["titleType"].isin(VALID_TITLE_TYPES)]
    df = df[df["isAdult"] == "0"]

    title_to_genres: dict[str, set[str]] = {}
    for _, row in df.iterrows():
        tconst = row["tconst"]
        if not tconst:
            continue
        genres = set()
        raw_genres = row.get("genres", "")
        if raw_genres and raw_genres != r"\N":
            genres = set(g.strip() for g in raw_genres.split(",") if g.strip())
        title_to_genres[tconst] = genres
        if max_titles and len(title_to_genres) >= max_titles:
            break
    return title_to_genres


def load_ratings(path: Path, selected_titles: set[str]) -> dict[str, float]:
    _ensure_gzip(path)
    ratings: dict[str, float] = {}
    with gzip.open(path, "rt", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            tconst = row["tconst"]
            if tconst not in selected_titles:
                continue
            try:
                ratings[tconst] = float(row["averageRating"])
            except (TypeError, ValueError):
                continue
    return ratings


def load_title_actors(path: Path, selected_titles: set[str]) -> dict[str, set[str]]:
    _ensure_gzip(path)
    title_to_actors: dict[str, set[str]] = defaultdict(set)

    with gzip.open(path, "rt", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            tconst = row["tconst"]
            if tconst not in selected_titles:
                continue
            if row.get("category") not in VALID_ACTOR_CATEGORIES:
                continue
            nconst = row.get("nconst")
            if not nconst or nconst == r"\N":
                continue
            title_to_actors[tconst].add(nconst)
    return title_to_actors


def build_actor_overlap_edges(
    title_to_actors: dict[str, set[str]],
) -> Counter[tuple[str, str]]:
    actor_to_titles: dict[str, list[str]] = defaultdict(list)
    for title, actors in title_to_actors.items():
        for actor in actors:
            actor_to_titles[actor].append(title)

    pair_counts: Counter[tuple[str, str]] = Counter()
    for titles in actor_to_titles.values():
        if len(titles) < 2:
            continue
        unique_titles = sorted(set(titles))
        for a, b in combinations(unique_titles, 2):
            pair_counts[(a, b)] += 1
    return pair_counts


def write_edges_csv(
    output_path: Path,
    pair_counts: Counter[tuple[str, str]],
    title_to_genres: dict[str, set[str]],
    ratings: dict[str, float],
    max_edges: int | None = None,
) -> int:
    items = sorted(pair_counts.items(), key=lambda item: item[1], reverse=True)
    if max_edges:
        items = items[:max_edges]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    written = 0

    with open(output_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "source",
                "target",
                "actors_common",
                "genres_common",
                "similaridade",
                "rating_media",
                "peso",
                "peso_bf",
            ]
        )

        for (source, target), actors_common in items:
            genres_common = len(title_to_genres.get(source, set()) & title_to_genres.get(target, set()))
            similaridade = (2 * actors_common) + genres_common
            if similaridade <= 0:
                continue

            rating_media = (ratings.get(source, 0.0) + ratings.get(target, 0.0)) / 2.0
            bonus_nota = 0.4 if rating_media >= 8.0 else 0.0
            peso = 1.0 / similaridade
            peso_bf = peso - bonus_nota

            writer.writerow(
                [
                    source,
                    target,
                    actors_common,
                    genres_common,
                    round(similaridade, 4),
                    round(rating_media, 4),
                    round(peso, 6),
                    round(peso_bf, 6),
                ]
            )
            written += 1

    return written


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gera dataset derivado IMDb (arestas entre filmes por ator em comum)."
    )
    parser.add_argument("--basics", required=True, help="Caminho para title.basics.tsv.gz")
    parser.add_argument("--principals", required=True, help="Caminho para title.principals.tsv.gz")
    parser.add_argument("--ratings", required=True, help="Caminho para title.ratings.tsv.gz")
    parser.add_argument(
        "--output",
        default="data/dataset_parte2/imdb_edges.csv",
        help="Arquivo de saida CSV de arestas derivadas",
    )
    parser.add_argument(
        "--max-titles",
        type=int,
        default=20000,
        help="Limite de filmes para controlar memoria/tempo",
    )
    parser.add_argument(
        "--max-edges",
        type=int,
        default=200000,
        help="Limite de arestas no CSV final",
    )
    args = parser.parse_args()

    basics_path = Path(args.basics)
    principals_path = Path(args.principals)
    ratings_path = Path(args.ratings)
    output_path = Path(args.output)

    print("1/4 Carregando titulos...")
    title_to_genres = load_titles(basics_path, max_titles=args.max_titles)
    selected_titles = set(title_to_genres.keys())
    print(f"Titulos selecionados: {len(selected_titles)}")

    print("2/4 Carregando notas...")
    ratings = load_ratings(ratings_path, selected_titles)
    print(f"Titulos com nota: {len(ratings)}")

    print("3/4 Carregando elenco...")
    title_to_actors = load_title_actors(principals_path, selected_titles)
    print(f"Titulos com elenco: {len(title_to_actors)}")

    print("4/4 Gerando arestas por ator em comum...")
    pair_counts = build_actor_overlap_edges(title_to_actors)
    written = write_edges_csv(
        output_path=output_path,
        pair_counts=pair_counts,
        title_to_genres=title_to_genres,
        ratings=ratings,
        max_edges=args.max_edges,
    )

    print(f"Arestas candidatas: {len(pair_counts)}")
    print(f"Arestas gravadas: {written}")
    print(f"Arquivo final: {output_path}")


if __name__ == "__main__":
    main()
