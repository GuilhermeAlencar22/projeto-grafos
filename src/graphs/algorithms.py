from collections import deque
import heapq

def bfs(graph, start):
    visited = set()
    queue = deque([start])
    order = []
    while queue:
        node = queue.popleft()
        if node not in visited:
            visited.add(node)
            order.append(node)
            for neighbor in graph[node]:
                if neighbor not in visited:
                    queue.append(neighbor)
    return order

def dfs(graph, start):
    visited = set()
    stack = [start]
    order = []
    while stack:
        node = stack.pop()
        if node not in visited:
            visited.add(node)
            order.append(node)
            for neighbor in graph[node]:
                if neighbor not in visited:
                    stack.append(neighbor)
    return order

def dijkstra(graph, start, end):
    dist = {node: float("inf") for node in graph}
    dist[start] = 0
    prev = {node: None for node in graph}
    heap = [(0, start)]

    while heap:
        current_dist, node = heapq.heappop(heap)

        if current_dist > dist[node]:
            continue
        if node == end:
            break
        for neighbor, weight in graph[node].items():
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

    return round(dist[end], 2), path