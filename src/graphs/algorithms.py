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

            for neighbor, _ in graph.neighbors(node):
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

            for neighbor, _ in graph.neighbors(node):
                if neighbor not in visited:
                    stack.append(neighbor)

    return order