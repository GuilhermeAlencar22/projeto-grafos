"""BFS: niveis num grafo pequeno; componente isolada (pre-requisito Parte 2)."""

from __future__ import annotations

from src.graphs.algorithms import bfs
from src.graphs.graph import Graph


def test_bfs_niveis_em_cadeia():
    g = Graph()
    g.add_edge("A", "B")
    g.add_edge("B", "C")

    order, levels = bfs(g, "A")

    assert order == ["A", "B", "C"]
    assert levels == {"A": 0, "B": 1, "C": 2}


def test_bfs_componente_isolada_e_alcancaveis():
    """Duas componentes: da fonte A so se visita {A,B}; da fonte X so {X}."""

    g = Graph()
    g.add_edge("A", "B")
    g.add_node("X")

    ord_ab, levels_ab = bfs(g, "A")
    assert set(ord_ab) == {"A", "B"}
    assert levels_ab == {"A": 0, "B": 1}
    assert "X" not in levels_ab

    ord_x, levels_x = bfs(g, "X")
    assert ord_x == ["X"]
    assert levels_x == {"X": 0}
