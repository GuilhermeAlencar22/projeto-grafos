from src.shared.graph import Graph
from src.shared.algorithms import bfs


def test_bfs_basico():
    g = Graph()
    g.add_edge("A", "B")
    g.add_edge("A", "C")
    g.add_edge("B", "D")

    resultado = bfs(g, "A")

    assert resultado[0] == "A"
    assert set(resultado) == {"A", "B", "C", "D"}


def test_bfs_niveis_em_cadeia():
    g = Graph()
    g.add_edge("A", "B")
    g.add_edge("B", "C")

    ordem, niveis = bfs(g, "A", return_levels=True)

    assert ordem == ["A", "B", "C"]
    assert niveis == {"A": 0, "B": 1, "C": 2}


def test_bfs_componente_isolada():
    g = Graph()
    g.add_edge("A", "B")
    g.add_node("X")

    ordem, niveis = bfs(g, "X", return_levels=True)

    assert ordem == ["X"]
    assert niveis == {"X": 0}
