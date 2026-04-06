from graphs.graph import Graph
from graphs.algorithms import dijkstra


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