"""DFS: ordem (grafo nao orientado na CLI); ciclo e classificacao de arestas (dirigido).

Requisito do enunciado: deteccao de ciclo e classificacao tree/back/forward/cross.
Isso usa `dfs_classificacao_dirigido` (grafo com `add_directed_edge`).
`dfs()` simples mantem compatibilidade com o restante do projeto.
"""

from __future__ import annotations

from src.graphs.algorithms import dfs, dfs_classificacao_dirigido
from src.graphs.graph import Graph


def test_dfs_ordem_vertices_alcancaveis():
    g = Graph()
    g.add_edge("A", "B")
    g.add_edge("B", "C")

    ordem = dfs(g, "A")

    assert ordem == ["A", "B", "C"]


def test_dfs_dirigido_sem_ciclo_so_arvore():
    g = Graph()
    g.add_directed_edge("A", "B", 1)
    g.add_directed_edge("B", "C", 1)

    ordem, tem_ciclo, arestas = dfs_classificacao_dirigido(g, "A")

    assert not tem_ciclo
    assert ordem == ["A", "B", "C"]
    tipos = [t for _, _, t in arestas]
    assert tipos == ["tree", "tree"]
    assert not any(t == "back" for t in tipos)


def test_dfs_dirigido_detecta_ciclo_aresta_back():
    g = Graph()
    g.add_directed_edge("A", "B", 1)
    g.add_directed_edge("B", "C", 1)
    g.add_directed_edge("C", "A", 1)

    _ordem, tem_ciclo, arestas = dfs_classificacao_dirigido(g, "A")

    assert tem_ciclo
    assert any(t == "back" for _, _, t in arestas)


def test_dfs_dirigido_classificacao_forward():
    """A->B->D e atalho A->D: aresta A->D visitada com D ja PRETO e entrada[A] < entrada[D]."""

    g = Graph()
    g.add_directed_edge("A", "B", 1)
    g.add_directed_edge("B", "D", 1)
    g.add_directed_edge("A", "D", 1)

    _ordem, tem_ciclo, arestas = dfs_classificacao_dirigido(g, "A")

    assert not tem_ciclo
    assert ("A", "D", "forward") in arestas


def test_dfs_dirigido_classificacao_cross():
    """Losango: C->D com D ja descoberto por B->D -> cross."""

    g = Graph()
    g.add_directed_edge("A", "B", 1)
    g.add_directed_edge("A", "C", 1)
    g.add_directed_edge("B", "D", 1)
    g.add_directed_edge("C", "D", 1)

    _ordem, tem_ciclo, arestas = dfs_classificacao_dirigido(g, "A")

    assert not tem_ciclo
    assert ("C", "D", "cross") in arestas
