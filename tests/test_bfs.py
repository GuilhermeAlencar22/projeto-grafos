from src.graphs.graph import Graph
from src.graphs.algorithms import bfs

def test_bfs():
    g = Graph()
    g.add_edge("A", "B")
    g.add_edge("B", "C")

    order, levels = bfs(g, "A")
    assert order == ["A", "B", "C"]
    assert levels == {"A": 0, "B": 1, "C": 2}