from collections import deque
import heapq


def _validar_pesos_nao_negativos(graph):
    """Levanta erro se existir aresta com peso negativo (requisito de Dijkstra)."""
    for u in graph.get_nodes():
        for v, w in graph.neighbors(u):
            if w < 0:
                raise ValueError(
                    f"Peso negativo nao permitido para Dijkstra: ({u}, {v}) = {w}"
                )


def validar_pesos_para_dijkstra(graph):
    """Uma varredura do grafo; chame antes de varias execucoes de dijkstra(...)."""
    _validar_pesos_nao_negativos(graph)


def dijkstra(graph, start, target):
    """
    Caminho minimo com pesos nao negativos (lista de adjacencia do grafo nao direcionado).

    Retorna (custo_total, caminho_como_lista) ou None se nao houver caminho.
    """
    if start not in graph.adj or target not in graph.adj:
        return None

    INF = float("inf")
    dist = {start: 0.0}
    pred = {start: None}
    pq = [(0.0, start)]

    while pq:
        d, u = heapq.heappop(pq)
        if u not in dist or d != dist[u]:
            continue
        if u == target:
            break
        for v, w in graph.neighbors(u):
            if w < 0:
                raise ValueError(
                    f"Peso negativo nao permitido para Dijkstra: ({u}, {v}) = {w}"
                )
            nd = d + w
            if nd < dist.get(v, INF):
                dist[v] = nd
                pred[v] = u
                heapq.heappush(pq, (nd, v))

    if target not in dist:
        return None

    caminho = []
    cur = target
    while cur is not None:
        caminho.append(cur)
        cur = pred[cur]
    caminho.reverse()
    return dist[target], caminho


def bfs(graph, start):
    """BFS com níveis (distância em arestas a partir de start).

    Marca vizinhos ao enfileirar para níveis corretos e evitar duplicatas na fila.
    Retorna (ordem_de_visita, dict_no -> nivel).
    """
    visited = {start}
    levels = {start: 0}
    queue = deque([start])
    order = [start]

    while queue:
        node = queue.popleft()
        for neighbor, _ in graph.neighbors(node):
            if neighbor not in visited:
                visited.add(neighbor)
                levels[neighbor] = levels[node] + 1
                queue.append(neighbor)
                order.append(neighbor)

    return order, levels


def dfs(graph, start):
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