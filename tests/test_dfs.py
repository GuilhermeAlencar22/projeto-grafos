from src.shared.graph import Graph
from src.shared.algorithms import dfs, dfs_classificacao_dirigido


def test_dfs_basico():
    g = Graph()
    g.add_edge("A", "B")
    g.add_edge("A", "C")
    g.add_edge("B", "D")

    resultado = dfs(g, "A")

    assert resultado[0] == "A"
    assert set(resultado) == {"A", "B", "C", "D"}


def test_dfs_dirigido_detecta_ciclo():
    g = Graph()
    g.add_directed_edge("A", "B", 1)
    g.add_directed_edge("B", "C", 1)
    g.add_directed_edge("C", "A", 1)

    _ordem, tem_ciclo, arestas = dfs_classificacao_dirigido(g, "A")

    assert tem_ciclo
    assert any(tipo == "back" for _, _, tipo in arestas)


def test_dfs_dirigido_classifica_arvore():
    g = Graph()
    g.add_directed_edge("A", "B", 1)
    g.add_directed_edge("B", "C", 1)

    ordem, tem_ciclo, arestas = dfs_classificacao_dirigido(g, "A")

    assert ordem == ["A", "B", "C"]
    assert not tem_ciclo
    assert [tipo for _, _, tipo in arestas] == ["tree", "tree"]
