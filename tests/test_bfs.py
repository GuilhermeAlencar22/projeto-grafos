from src.graphs.graph import Graph
from src.graphs.algorithms import bfs

def test_bfs():
    g = Graph()
    g.add_edge("A", "B")
    g.add_edge("B", "C")

    result = bfs(g, "A")
    assert result == ["A", "B", "C"]