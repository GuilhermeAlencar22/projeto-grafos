"""algoritmos principais do projeto."""

from collections import deque
import heapq


def validar_pesos_para_dijkstra(graph):
    for u in graph.get_nodes():
        for v, w in graph.neighbors(u):
            if w < 0:
                raise ValueError(
                    f"dijkstra: peso negativo nao permitido ({u}, {v}) w={w}"
                )


def dijkstra(graph, start, target):
    if start not in graph or target not in graph:
        return float("inf"), []

    dist = {start: 0.0}
    pred = {start: None}
    heap = [(0.0, start)]

    while heap:
        current_dist, node = heapq.heappop(heap)
        if current_dist != dist.get(node):
            continue
        if node == target:
            break

        for neighbor, weight in graph.neighbors(node):
            if weight < 0:
                raise ValueError(
                    f"dijkstra: peso negativo nao permitido ({node}, {neighbor}) w={weight}"
                )
            new_dist = current_dist + weight
            if new_dist < dist.get(neighbor, float("inf")):
                dist[neighbor] = new_dist
                pred[neighbor] = node
                heapq.heappush(heap, (new_dist, neighbor))

    if target not in dist:
        return float("inf"), []

    path = []
    cur = target
    while cur is not None:
        path.append(cur)
        cur = pred[cur]
    path.reverse()
    return dist[target], path


def bellman_ford(graph, start):
    if start not in graph:
        raise ValueError(f"no inicial inexistente no grafo: {start}")

    nodes = graph.get_nodes()
    dist = {v: float("inf") for v in nodes}
    dist[start] = 0.0

    for _ in range(max(0, len(nodes) - 1)):
        alterou = False
        for u in nodes:
            if dist[u] == float("inf"):
                continue
            for v, w in graph.neighbors(u):
                nd = dist[u] + w
                if nd < dist[v]:
                    dist[v] = nd
                    alterou = True
        if not alterou:
            break

    for u in nodes:
        if dist[u] == float("inf"):
            continue
        for v, w in graph.neighbors(u):
            if dist[u] + w < dist[v]:
                return True, None

    return False, dist


def bfs(graph, start, return_levels=False):
    if start not in graph:
        return ([], {}) if return_levels else []

    visited = {start}
    levels = {start: 0}
    queue = deque([start])
    order = []

    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor, _ in graph.neighbors(node):
            if neighbor not in visited:
                visited.add(neighbor)
                levels[neighbor] = levels[node] + 1
                queue.append(neighbor)

    return (order, levels) if return_levels else order


def dfs(graph, start):
    if start not in graph:
        return []

    visited = set()
    stack = [start]
    order = []

    while stack:
        node = stack.pop()
        if node not in visited:
            visited.add(node)
            order.append(node)
            for neighbor, _ in graph.neighbors(node):
                if neighbor not in visited:
                    stack.append(neighbor)

    return order


_BRANCO, _CINZA, _PRETO = 0, 1, 2


def dfs_classificacao_dirigido(graph, start):
    if start not in graph:
        return [], False, []

    entrada = {}
    estado = {}
    relogio = [0]
    ordem_pre = []
    arestas = []
    tem_ciclo = False

    def visitar(u):
        nonlocal tem_ciclo
        estado[u] = _CINZA
        relogio[0] += 1
        entrada[u] = relogio[0]
        ordem_pre.append(u)

        for v, _ in graph.neighbors(u):
            cor_v = estado.get(v, _BRANCO)
            if cor_v == _BRANCO:
                arestas.append((u, v, "tree"))
                visitar(v)
            elif cor_v == _CINZA:
                arestas.append((u, v, "back"))
                tem_ciclo = True
            else:
                tipo = "forward" if entrada[u] < entrada[v] else "cross"
                arestas.append((u, v, tipo))

        estado[u] = _PRETO

    visitar(start)
    return ordem_pre, tem_ciclo, arestas
