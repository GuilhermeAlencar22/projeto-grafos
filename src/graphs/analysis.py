from collections import deque

from graphs.graph import Graph


def componente_alcancavel(graph: Graph, start: str) -> list:
    if start not in graph.adj:
        return []
    visitados = {start}
    fila = deque([start])
    ordem = []
    while fila:
        u = fila.popleft()
        ordem.append(u)
        for v, _ in graph.neighbors(u):
            if v not in visitados:
                visitados.add(v)
                fila.append(v)
    return ordem


def componente_tem_ciclo(graph: Graph, vertices: list) -> bool:
    verts = set(vertices)
    n = len(verts)
    if n < 3:
        return False
    arestas = set()
    for u in verts:
        for v, _ in graph.neighbors(u):
            if v in verts:
                a, b = (u, v) if u < v else (v, u)
                arestas.add((a, b))
    m = len(arestas)
    return m > n - 1
