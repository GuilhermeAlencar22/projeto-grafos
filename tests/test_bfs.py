from graphs.graph import Graph
from graphs.algorithms import bfs


def test_bfs_basico():
    g = Graph()
    g.add_edge("A", "B")
    g.add_edge("A", "C")
    g.add_edge("B", "D")

    resultado = bfs(g, "A")

    assert resultado[0] == "A"
    assert set(resultado) == {"A", "B", "C", "D"}