import csv
from graphs.graph import Graph


def carregar_aeroportos(path):
    aeroportos = {}

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            codigo = row.get("iata")

            if not codigo:
                continue

            aeroportos[codigo] = {
                "cidade": row.get("cidade", ""),
                "regiao": row.get("regiao", "")
            }

    return aeroportos


def carregar_grafo(path):
    grafo = Graph()

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            u = row.get("origem")
            v = row.get("destino")

            if not u or not v:
                continue

            try:
                peso = float(row.get("peso", 1.0))
            except:
                peso = 1.0

            grafo.add_edge(u, v, peso)

    return grafo