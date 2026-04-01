import csv
from collections import defaultdict

def carregar_aeroportos(path):
    aeroportos = {}

    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            aeroportos[row["iata"]] = {
                "cidade": row["cidade"],
                "regiao": row["regiao"]
            }

    return aeroportos

def carregar_grafo(path):
    grafo = defaultdict(dict)

    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            a = row["origem"]
            b = row["destino"]
            peso = float(row["peso"])

            grafo[a][b] = peso
            grafo[b][a] = peso

    return grafo