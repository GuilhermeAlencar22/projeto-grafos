"""

Gera data/dataset_parte2/imdb_bellman_ford.csv a partir de title.principals e title.ratings.



Uso (no diretorio do projeto ou com caminhos absolutos):

  python src/parte2/build_bellman_dataset.py --principals caminho/title.principals.tsv \\

      --ratings caminho/title.ratings.tsv



Opcional (somente titulos titleType=movie):

  python src/parte2/build_bellman_dataset.py ... --basics caminho/title.basics.tsv.gz



Arquivos .tsv.gz tambem sao aceitos.

"""



from __future__ import annotations



import argparse

import csv

import gzip

from collections import Counter, defaultdict

from itertools import combinations

from pathlib import Path



VALID_ACTOR_CATEGORIES = {"actor", "actress", "self"}



SCRIPT_DIR = Path(__file__).resolve().parent

PROJECT_ROOT = SCRIPT_DIR.parent.parent

DEFAULT_OUTPUT = PROJECT_ROOT / "data/dataset_parte2/imdb_bellman_ford.csv"

PESO_DECIMALS = 6





def _open_text(path: Path):

    """Abre TSV texto; se o nome termina em .gz, descompacta."""

    raw = path.expanduser().resolve()

    if raw.suffix == ".gz" or str(raw).endswith(".gz"):

        return gzip.open(raw, "rt", encoding="utf-8", newline="")

    return open(raw, "r", encoding="utf-8", newline="")





def load_movie_tconsts(path: Path) -> set[str]:

    """tconst com titleType == movie (para filtro opcional via title.basics)."""

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

    """filme (tconst) -> averageRating."""

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





def load_title_actors(path: Path, valid_titles: set[str]) -> dict[str, set[str]]:

    """filme -> conjunto de nconst (atores) para titulos que tem nota."""

    title_to_actors: dict[str, set[str]] = defaultdict(set)

    with _open_text(path) as fh:

        reader = csv.DictReader(fh, delimiter="\t")

        for row in reader:

            tconst = row.get("tconst")

            if not tconst or tconst not in valid_titles:

                continue

            if row.get("category") not in VALID_ACTOR_CATEGORIES:

                continue

            nconst = row.get("nconst")

            if not nconst or nconst == r"\N":

                continue

            title_to_actors[tconst].add(nconst)

    return title_to_actors





def count_distinct_actors(title_to_actors: dict[str, set[str]]) -> int:

    unicos: set[str] = set()

    for actors in title_to_actors.values():

        unicos.update(actors)

    return len(unicos)





def build_pair_common_actors(

    title_to_actors: dict[str, set[str]],

) -> Counter[tuple[str, str]]:

    """

    Para cada par de filmes que compartilham pelo menos um ator,

    conta quantos atores em comum.



    Titulos por ator sao deduplicados (set) antes das combinacoes.

    Chaves (a, b) com a < b na ordenacao lexicografica dos ids.

    """

    actor_to_titles: dict[str, set[str]] = defaultdict(set)

    for title, actors in title_to_actors.items():

        for actor in actors:

            actor_to_titles[actor].add(title)



    pair_counts: Counter[tuple[str, str]] = Counter()

    for titles_set in actor_to_titles.values():

        if len(titles_set) < 2:

            continue

        unique_titles = sorted(titles_set)

        for a, b in combinations(unique_titles, 2):

            pair_counts[(a, b)] += 1

    return pair_counts





def build_directed_edges(

    pair_counts: Counter[tuple[str, str]],

    ratings: dict[str, float],

) -> dict[tuple[str, str], float]:

    """

    A -> B somente se rating(B) > rating(A).

    peso = 2 - atores_em_comum - (rating_B - rating_A)

    Sem duplicar (source, target): um unico peso por arco.

    """

    edges: dict[tuple[str, str], float] = {}

    for (a, b), k in pair_counts.items():

        # k = quantidade de atores em comum entre os dois titulos (a, b).

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

        # diff = diferenca de rating entre target e source (sempre > 0 neste ramo).

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

            peso = round(edges[(source, target)], PESO_DECIMALS)

            w.writerow([source, target, peso])

            count += 1

    return count





def main() -> None:

    parser = argparse.ArgumentParser(

        description="Constroi imdb_bellman_ford.csv a partir de principals + ratings."

    )

    parser.add_argument(

        "--principals",

        type=Path,

        default=Path("title.principals.tsv"),

        help="title.principals.tsv ou .tsv.gz (padrao: ./title.principals.tsv)",

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

    args = parser.parse_args()



    print("Carregando ratings...")

    ratings = load_ratings(args.ratings)

    n_rating_total = len(ratings)



    valid = set(ratings.keys())

    if args.basics is not None:

        print("Aplicando filtro title.basics (apenas movie)...")

        movies = load_movie_tconsts(args.basics)

        valid &= movies

        ratings = {t: ratings[t] for t in valid if t in ratings}

        print(f"   Titulos com rating apos filtro basics: {len(ratings)}")



    print("Carregando elenco (principals)...")

    title_to_actors = load_title_actors(args.principals, valid)

    print(f"   Titulos com rating e elenco: {len(title_to_actors)}")



    print("Contando pares com atores em comum (titulos deduplicados por ator)...")

    pair_counts = build_pair_common_actors(title_to_actors)

    print(f"   Pares candidatos: {len(pair_counts)}")



    print("Gerando arcos dirigidos do menor rating para o maior rating...")

    edges = build_directed_edges(pair_counts, ratings)

    out_path = args.output.resolve()

    n_arcos = write_csv(args.output, edges)



    n_atores = count_distinct_actors(title_to_actors)

    n_filmes_usados = len(title_to_actors)



    print()

    print("--- Resumo ---")

    print(f"  Filmes com rating usados (com pelo menos um ator): {n_filmes_usados}")

    if args.basics is not None:

        print(f"  Titulos com rating na base (antes do filtro basics): {n_rating_total}")

    else:

        print(f"  Titulos com rating na base: {n_rating_total}")

    print(f"  Atores distintos considerados: {n_atores}")

    print(f"  Arcos dirigidos gerados: {n_arcos}")

    print(f"  Arquivo salvo: {out_path}")





if __name__ == "__main__":

    main()


