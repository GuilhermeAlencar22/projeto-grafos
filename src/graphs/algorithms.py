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


def bellman_ford(graph, start):
    """
    Caminhos minimos a partir de `start` em grafo dirigido (pesos reais, negativos ok).

    Retorna (ciclo_negativo, distancias):
    - (True, None) se existir ciclo de custo total negativo alcanavel a partir de `start`
      (as distancias nao sao validas; nao use o segundo retorno).
    - (False, dist) em que `dist[v]` e o custo minimo de `start` a `v`, ou inf se `v`
      nao e alcanavel.
    """
    if start not in graph.adj:
        raise ValueError(f"No inicial inexistente no grafo: {start}")

    nodes = graph.get_nodes()
    n = len(nodes)
    INF = float("inf")
    dist = {v: INF for v in nodes}
    dist[start] = 0.0

    for _ in range(max(0, n - 1)):
        alterou = False
        for u in nodes:
            du = dist[u]
            if du == INF:
                continue
            for v, w in graph.neighbors(u):
                nd = du + w
                if nd < dist[v]:
                    dist[v] = nd
                    alterou = True
        if not alterou:
            break

    for u in nodes:
        du = dist[u]
        if du == INF:
            continue
        for v, w in graph.neighbors(u):
            if du + w < dist[v]:
                return True, None

    return False, dist


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