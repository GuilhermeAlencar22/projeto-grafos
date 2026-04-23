"""monta imdb_bellman_ford.csv ligando filmes por diretor em comum e pela nota."""

from __future__ import annotations

import argparse

import csv

import gzip

from collections import Counter, defaultdict

from itertools import combinations

from pathlib import Path

VALID_DIRECTOR_CATEGORY = "director"

SCRIPT_DIR = Path(__file__).resolve().parent

PROJECT_ROOT = SCRIPT_DIR.parent.parent

DEFAULT_OUTPUT = PROJECT_ROOT / "data/dataset_parte2/imdb_bellman_ford.csv"

def _open_text(path: Path):

    raw = path.expanduser().resolve()

    if raw.suffix == ".gz" or str(raw).endswith(".gz"):

        return gzip.open(raw, "rt", encoding="utf-8", newline="")

    return open(raw, "r", encoding="utf-8", newline="")

def load_movie_tconsts(path: Path) -> set[str]:

    out: set[str] = set()

    with _open_text(path) as fh:

        reader = csv.DictReader(fh, delimiter="\t")

        for row in reader:

            if row.get("titleType") != "movie":

                continue

            tconst = row.get("tconst")

            if tconst:

                out.add(tconst)

    return out

def load_ratings(path: Path) -> dict[str, float]:

    out: dict[str, float] = {}

    with _open_text(path) as fh:

        reader = csv.DictReader(fh, delimiter="\t")

        for row in reader:

            tconst = row.get("tconst")

            if not tconst:

                continue

            try:

                out[tconst] = float(row["averageRating"])

            except (KeyError, ValueError, TypeError):

                continue

    return out

def load_title_directors(
    path: Path,
    valid_titles: set[str],
    *,
    max_directors: int | None = None,
    progress_step: int | None = None,
) -> dict[str, set[str]]:

    title_to_directors: dict[str, set[str]] = defaultdict(set)

    directors_in_scope: set[str] = set()

    linhas_lidas = 0

    with _open_text(path) as fh:

        reader = csv.DictReader(fh, delimiter="\t")

        for row in reader:

            linhas_lidas += 1

            if progress_step and linhas_lidas % progress_step == 0:

                print(f"   principals: {linhas_lidas} linhas lidas")

            tconst = row.get("tconst")

            if not tconst or tconst not in valid_titles:

                continue

            if row.get("category") != VALID_DIRECTOR_CATEGORY:

                continue

            nconst = row.get("nconst")

            if not nconst or nconst == r"\N":

                continue

            if max_directors is not None:

                if nconst not in directors_in_scope:

                    if len(directors_in_scope) >= max_directors:

                        break

                    directors_in_scope.add(nconst)

            title_to_directors[tconst].add(nconst)

            if max_directors is not None and len(directors_in_scope) >= max_directors:

                break

    if progress_step:

        print(f"   principals: total {linhas_lidas} linhas lidas")

    return title_to_directors

def count_distinct_directors(title_to_directors: dict[str, set[str]]) -> int:

    unicos: set[str] = set()

    for diretores in title_to_directors.values():

        unicos.update(diretores)

    return len(unicos)

def build_pair_common_directors(

    title_to_directors: dict[str, set[str]],

) -> Counter[tuple[str, str]]:

    director_to_titles: dict[str, set[str]] = defaultdict(set)

    for title, diretores in title_to_directors.items():

        for diretor in diretores:

            director_to_titles[diretor].add(title)

    pair_counts: Counter[tuple[str, str]] = Counter()

    for _diretor, titulos_do_diretor in director_to_titles.items():

        titulos_unicos = sorted(set(titulos_do_diretor))

        if len(titulos_unicos) < 2:

            continue

        for a, b in combinations(titulos_unicos, 2):

            pair_counts[(a, b)] += 1

    return pair_counts

def build_directed_edges(

    pair_counts: Counter[tuple[str, str]],

    ratings: dict[str, float],

) -> dict[tuple[str, str], float]:

    edges: dict[tuple[str, str], float] = {}

    for (a, b), k in pair_counts.items():

        # k: diretores em comum neste par de titulos

        ra = ratings.get(a)

        rb = ratings.get(b)

        if ra is None or rb is None:

            continue

        if rb == ra:

            continue

        if rb > ra:

            source, target = a, b

            diff = rb - ra

        else:

            source, target = b, a

            diff = ra - rb

        # diff positivo: rating do alvo maior que o da fonte (este ramo)

        peso = 2.0 - k - diff

        edges[(source, target)] = peso

    return edges

def write_csv(output_path: Path, edges: dict[tuple[str, str], float]) -> int:

    output_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0

    with open(output_path, "w", encoding="utf-8", newline="") as fh:

        w = csv.writer(fh)

        w.writerow(["source", "target", "peso"])

        for (source, target) in sorted(edges.keys()):

            peso = round(edges[(source, target)], 6)

            w.writerow([source, target, peso])

            count += 1

    return count

def main() -> None:

    parser = argparse.ArgumentParser(

        description=(

            "Constroi imdb_bellman_ford.csv (diretores em comum, principals category=director + ratings)."

        ),

    )

    parser.add_argument(

        "--principals",

        type=Path,

        default=Path("title.principals.tsv"),

        help=(

            "title.principals.tsv ou .tsv.gz — usa apenas linhas category=director "

            "(padrao: ./title.principals.tsv)"

        ),

    )

    parser.add_argument(

        "--ratings",

        type=Path,

        default=Path("title.ratings.tsv"),

        help="title.ratings.tsv ou .tsv.gz (padrao: ./title.ratings.tsv)",

    )

    parser.add_argument(

        "--output",

        type=Path,

        default=DEFAULT_OUTPUT,

        help=f"Saida CSV (padrao: {DEFAULT_OUTPUT})",

    )

    parser.add_argument(

        "--basics",

        type=Path,

        default=None,

        help=(

            "Opcional: title.basics.tsv / .gz — restringe a titulos com titleType=movie "

            "(intersecao com titulos que tem rating)."

        ),

    )

    parser.add_argument(

        "--max-edges",

        type=int,

        default=None,

        help=(

            "Opcional: limita quantos arcos sao escritos (ordenacao deterministica "

            "por source e target). Util para testes sem CSV gigante."

        ),

    )

    parser.add_argument(

        "--max-directors",

        type=int,

        default=None,

        help=(

            "Opcional: numero maximo de diretores distintos (nconst); ordem = aparecimento "

            "no principals. Encerra a leitura do arquivo assim que esse limite e atingido "

            "(nao varre o restante do .tsv/.gz)."

        ),

    )

    parser.add_argument(

        "--progress-step",

        type=int,

        default=None,

        help="Opcional: imprime progresso a cada N linhas lidas de title.principals.",

    )

    args = parser.parse_args()

    if args.progress_step is not None and args.progress_step <= 0:

        raise SystemExit("ERRO: --progress-step deve ser um inteiro positivo.")

    if args.max_directors is not None and args.max_directors < 0:

        raise SystemExit("ERRO: --max-directors nao pode ser negativo.")

    print("Carregando ratings...")

    ratings = load_ratings(args.ratings)

    n_titulos_com_rating_na_base = len(ratings)

    valid = set(ratings.keys())

    if args.basics is not None:

        print("Aplicando filtro title.basics (apenas movie)...")

        movies = load_movie_tconsts(args.basics)

        valid &= movies

        ratings = {t: ratings[t] for t in valid if t in ratings}

        print(f"   Titulos com rating apos filtro basics: {len(ratings)}")

    print("Carregando diretores (principals, category=director)...")

    if args.max_directors is not None:

        print(f"   Limite ativo: --max-directors={args.max_directors}")

    title_to_directors = load_title_directors(
        args.principals,
        valid,
        max_directors=args.max_directors,
        progress_step=args.progress_step,
    )

    print(f"   Titulos com rating e pelo menos um diretor: {len(title_to_directors)}")

    print("Contando pares com diretores em comum (titulos deduplicados por diretor)...")

    pair_counts = build_pair_common_directors(title_to_directors)

    print(f"   Pares candidatos: {len(pair_counts)}")

    print("Gerando arcos dirigidos do menor rating para o maior rating...")

    edges = build_directed_edges(pair_counts, ratings)

    if args.max_edges is not None and len(edges) > args.max_edges:

        ordem = sorted(edges.keys())

        edges = {k: edges[k] for k in ordem[: args.max_edges]}

        print(f"   Aplicado --max-edges={args.max_edges} (ordenacao lexicografica).")

    out_path = args.output.resolve()

    n_arcos = write_csv(args.output, edges)

    n_diretores = count_distinct_directors(title_to_directors)

    n_filmes_com_rating_usados = len(title_to_directors)

    caminho_absoluto = str(out_path.resolve())

    print()

    print("--- Resumo ---")

    print(f"  Filmes com rating usados: {n_filmes_com_rating_usados}")

    print(f"  Titulos com rating na base: {n_titulos_com_rating_na_base}")

    print(f"  Diretores distintos considerados: {n_diretores}")

    print(f"  Arcos dirigidos gerados: {n_arcos}")

    print(f"  Arquivo salvo (caminho absoluto): {caminho_absoluto}")

if __name__ == "__main__":

    main()

