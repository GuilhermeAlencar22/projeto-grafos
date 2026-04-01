import json
import csv
from graphs.algorithms import dijkstra

from utils.metrics import (
    metricas_globais,
    subgrafo_por_regiao,
    ego_network_metrics,
    calcular_graus
)

from graphs.io import carregar_aeroportos, carregar_grafo
def salvar_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def salvar_csv(path, data):
    if not data:
        return

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

def main():
    aeroportos = carregar_aeroportos("data/aeroportos_data.csv")
    grafo = carregar_grafo("data/adjacencias_aeroportos.csv")

    global_metrics = metricas_globais(grafo)
    salvar_json("out/global.json", global_metrics)

    regioes = subgrafo_por_regiao(grafo, aeroportos)
    salvar_json("out/regioes.json", regioes)

    ego = ego_network_metrics(grafo)
    salvar_csv("out/ego_aeroportos.csv", ego)

    graus = sorted(calcular_graus(grafo), key=lambda x: x["grau"], reverse=True)
    salvar_csv("out/graus.csv", graus)

    mais_conectado = graus[0] if graus else None
    mais_denso = max(ego, key=lambda x: x["densidade_ego"]) if ego else None

    rankings = {
        "mais_conectado": mais_conectado,
        "maior_densidade_local": mais_denso
    }

    salvar_json("out/rankings.json", rankings)

    rotas = []
    with open("data/rotas.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            origem = row["origem"]
            destino = row["destino"]
            custo, caminho = dijkstra(grafo, origem, destino)
            rotas.append({
                "origem": origem,
                "destino": destino,
                "custo": custo,
                "caminho": " -> ".join(caminho) if caminho else "sem caminho"
            })
    salvar_csv("out/distancias_rotas.csv", rotas)

if __name__ == "__main__":
    main()