from graphs.graph import Graph
from graphs.algorithms import dfs


def test_dfs_basico():
    g = Graph()
    g.add_edge("A", "B")
    g.add_edge("A", "C")
    g.add_edge("B", "D")

    resultado = dfs(g, "A")

    assert resultado[0] == "A"
    assert set(resultado) == {"A", "B", "C", "D"}