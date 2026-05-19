import pytest

from src.graphs.graph import Graph
from src.graphs.algorithms import dijkstra, validar_pesos_para_dijkstra


def test_dijkstra_caminho_simples():
    g = Graph()
    g.add_edge("A", "B", 1)
    g.add_edge("B", "C", 2)
    g.add_edge("A", "C", 5)

    custo, caminho = dijkstra(g, "A", "C")

    assert custo == 3
    assert caminho == ["A", "B", "C"]


def test_dijkstra_sem_caminho():
    g = Graph()
    g.add_edge("A", "B", 1)
    g.add_node("C")

    custo, caminho = dijkstra(g, "A", "C")

    assert custo == float("inf")
    assert caminho == []


@pytest.mark.parametrize(
    "fn",
    [validar_pesos_para_dijkstra, lambda g: dijkstra(g, "A", "B")],
)
def test_dijkstra_rejeita_peso_negativo(fn):
    g = Graph()
    g.add_edge("A", "B", -1.0)

    with pytest.raises(ValueError, match="peso negativo"):
        fn(g)
