"""dijkstra: custo/caminho com peso >= 0; peso negativo tem que falhar."""

from __future__ import annotations

import pytest

from src.graphs.algorithms import dijkstra, validar_pesos_para_dijkstra
from src.graphs.graph import Graph


def test_dijkstra_custo_e_caminho_pesos_nao_negativos():
    g = Graph()
    g.add_edge("A", "B", 1.0)
    g.add_edge("B", "C", 4.0)
    g.add_edge("A", "C", 10.0)

    res = dijkstra(g, "A", "C")

    assert res is not None
    custo, caminho = res
    assert custo == 5.0
    assert caminho == ["A", "B", "C"]


@pytest.mark.parametrize(
    "fn",
    [validar_pesos_para_dijkstra, lambda g: dijkstra(g, "A", "B")],
    ids=["antes_da_busca", "durante_relaxacao"],
)
def test_dijkstra_rejeita_peso_negativo(fn):
    g = Graph()
    g.add_edge("A", "B", -1.0)

    with pytest.raises(ValueError, match="peso negativo"):
        fn(g)
