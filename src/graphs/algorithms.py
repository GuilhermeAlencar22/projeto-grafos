"""implementa menor caminho, bellman-ford e as buscas em largura e profundidade."""

from collections import deque
import heapq


def _validar_pesos_nao_negativos(graph):
    for u in graph.get_nodes():
        for v, w in graph.neighbors(u):
            if w < 0:
                raise ValueError(
                    f"Peso negativo nao permitido para Dijkstra: ({u}, {v}) = {w}"
                )


def validar_pesos_para_dijkstra(graph):
    _validar_pesos_nao_negativos(graph)


def dijkstra(graph, start, target):
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


# DFS com cores (branco/cinza/preto) para grafo dirigido — classificacao de arestas e ciclo.
_BRANCO, _CINZA, _PRETO = 0, 1, 2


def dfs_classificacao_dirigido(graph, start):
    """
    DFS a partir de `start` apenas na componente alcancavel (por arestas de saida).

    Retorna:
        ordem_pre: ordem de primeira descoberta (pre-order)
        tem_ciclo: True se existir aresta de retorno (back) no trecho visitado
        arestas: lista de (u, v, tipo) com tipo em tree, back, forward, cross

    Regra para aresta (u,v) com v ja PRETO: forward se entrada[u] < entrada[v], senao cross.
    """
    if start not in graph.adj:
        return [], False, []

    entrada: dict[str, int] = {}
    estado: dict[str, int] = {}
    relogio = [0]
    ordem_pre: list[str] = []
    arestas: list[tuple[str, str, str]] = []
    tem_ciclo = False

    def visitar(u: str) -> None:
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
                if entrada[u] < entrada[v]:
                    arestas.append((u, v, "forward"))
                else:
                    arestas.append((u, v, "cross"))

        estado[u] = _PRETO

    visitar(start)
    return ordem_pre, tem_ciclo, arestas