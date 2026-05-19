"""loader load_edge_csv_graph na parte 2 (csv temporario)."""

from __future__ import annotations

from src.graphs.io import load_edge_csv_graph


def test_load_edge_csv_grafo_nao_orientado(tmp_path):
    p = tmp_path / "mini.csv"
    p.write_text(
        "source,target,peso\n"
        "A,B,1.0\n"
        "B,C,2.0\n",
        encoding="utf-8",
    )

    dados = load_edge_csv_graph(str(p))

    assert set(dados.keys()) == {"A", "B", "C"}
    assert dados["A"] == [("B", 1.0)]
    assert dados["C"] == [("B", 2.0)]
    b_viz = sorted(dados["B"], key=lambda t: t[0])
    assert b_viz == [("A", 1.0), ("C", 2.0)]
