import csv
from graphs.graph import Graph

def carregar_aeroportos(path):
    aeroportos = {}
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            codigo = row.get("iata", "").strip()
            if not codigo:
                continue
            aeroportos[codigo] = {
                "cidade": row.get("cidade", "").strip(),
                "regiao": row.get("regiao", "").strip()
            }
    return aeroportos

def carregar_grafo(path):
    grafo = Graph()
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            u = row.get("origem", "").strip()
            v = row.get("destino", "").strip()
            if not u or not v:
                continue
            try:
                peso = float(row.get("peso", 1.0))
            except (ValueError, TypeError):
                peso = 1.0
            grafo.add_edge(u, v, peso)
    return grafo