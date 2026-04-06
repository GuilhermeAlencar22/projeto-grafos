from collections import deque
import heapq


def bfs(graph, start):
    if start not in graph:
        return []

    visited = set([start])
    queue = deque([start])
    order = []

    while queue:
        node = queue.popleft()
        order.append(node)

        for neighbor, _ in graph.neighbors(node):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    return order


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


def dijkstra(graph, start, end):
    if start not in graph or end not in graph:
        return float("inf"), []

    dist = {node: float("inf") for node in graph.get_nodes()}
    prev = {node: None for node in graph.get_nodes()}

    dist[start] = 0
    heap = [(0, start)]

    while heap:
        current_dist, node = heapq.heappop(heap)

        if current_dist > dist[node]:
            continue

        if node == end:
            break

        for neighbor, weight in graph.neighbors(node):
            new_dist = current_dist + weight

            if new_dist < dist[neighbor]:
                dist[neighbor] = new_dist
                prev[neighbor] = node
                heapq.heappush(heap, (new_dist, neighbor))


    path = []
    cur = end

    if dist[end] == float("inf"):
        return float("inf"), []

    while cur is not None:
        path.append(cur)
        cur = prev[cur]

    path.reverse()

    return dist[end], path