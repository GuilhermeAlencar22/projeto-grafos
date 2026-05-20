from src.shared.algorithms import bellman_ford
from src.shared.graph import Graph


def test_bellman_ford_negativos_sem_ciclo_negativo_distancias():
    g = Graph()
    g.add_directed_edge("A", "B", -2.0)
    g.add_directed_edge("B", "C", 3.0)

    ciclo_neg, dist = bellman_ford(g, "A")

    assert ciclo_neg is False
    assert dist is not None
    assert dist["A"] == 0.0
    assert dist["B"] == -2.0
    assert dist["C"] == 1.0


def test_bellman_ford_detecta_ciclo_negativo():
    g = Graph()
    g.add_directed_edge("A", "B", 1.0)
    g.add_directed_edge("B", "C", 1.0)
    g.add_directed_edge("C", "A", -5.0)

    ciclo_neg, dist = bellman_ford(g, "A")

    assert ciclo_neg is True
    assert dist is None
