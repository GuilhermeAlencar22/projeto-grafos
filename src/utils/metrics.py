from collections import defaultdict
import json
import csv


def calcular_densidade(n, e):
    if n < 2:
        return 0
    return (2 * e) / (n * (n - 1))


def metricas_globais(grafo):
    V = len(grafo)
    E = len(grafo.edges())

    return {
        "ordem": V,
        "tamanho": E,
        "densidade": calcular_densidade(V, E)
    }


def subgrafo_por_regiao(grafo, aeroportos_info):
    regioes = defaultdict(set)

    for codigo, info in aeroportos_info.items():
        regioes[info["regiao"]].add(codigo)

    resultado = []

    for regiao, vertices in regioes.items():
        V = len(vertices)
        E = 0

        for v in vertices:
            for u in grafo[v].keys():
                if u in vertices:
                    E += 1

        E = E // 2
        densidade = calcular_densidade(V, E)
        resultado.append({
            "regiao": regiao,
            "ordem": V,
            "tamanho": E,
            "densidade": densidade
        })

    return resultado

def calcular_graus(grafo):
    graus = []

    for v in grafo.get_nodes():
        graus.append({
            "aeroporto": v,
            "grau": len(grafo[v])
        })

    return graus

def ego_network_metrics(grafo):
    resultado = []

    for v in grafo.get_nodes():
        vizinhos = set(grafo[v])
        ego_vertices = vizinhos.union({v})
        V = len(ego_vertices)
        E = 0
        for u in ego_vertices:
            for w in grafo[u].keys():
                if w in ego_vertices:
                    E += 1

        E = E // 2
        densidade = calcular_densidade(V, E)

        resultado.append({
            "aeroporto": v,
            "grau": len(grafo[v]),
            "ordem_ego": V,
            "tamanho_ego": E,
            "densidade_ego": densidade
        })

    return resultado