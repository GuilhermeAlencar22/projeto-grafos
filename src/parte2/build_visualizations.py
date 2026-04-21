"""monta figuras png a partir do relatorio json e do csv de arestas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# tamanho da figura, dpi, cores e fontes nos graficos
FIG_WIDE = (10.5, 5.8)
FIG_SCATTER = (9.2, 6.2)
FIG_COMPS = (10.5, 8.2)
FIG_DPI = 200
GRID_ALPHA = 0.35

FONT_TITLE = 13
FONT_AXIS = 11
FONT_LEGEND = 9
COLOR_GRID = "#bbbbbb"
COLOR_EDGE_BAR = "#333333"

COL_GRAD_DIST = "#238b45"
COL_COMPS_LINE = "#d95f02"
COL_COMPS_MARK_FACE = "#fed976"
COL_COMPS_MARK_EDGE = "#b35806"
COL_SCATTER_ACTORS = "#1b9e77"
COL_SCATTER_SIM_PESO = "#542788"
COL_CURVA_MODELO = "#b35806"
COL_BENCHMARK = ["#2c7bb6", "#abd9e9", "#fdae61", "#d7191c"]
COL_COMPS_BAR = ["#91bfdb", "#d73027"]

SCATTER_SEED_ATORES = 42
SCATTER_SEED_SIM_PESO = 44


def _aplicar_estilo_relatorio() -> None:
    plt.rcParams.update(
        {
            "font.size": FONT_AXIS,
            "axes.titlesize": FONT_TITLE,
            "axes.labelsize": FONT_AXIS,
            "legend.fontsize": FONT_LEGEND,
            "grid.color": COLOR_GRID,
        }
    )


def _salvar_fig(fig: plt.Figure, path_png: Path) -> None:
    path_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path_png, dpi=FIG_DPI, bbox_inches="tight")


def _grid_leve(ax: plt.Axes) -> None:
    ax.grid(True, linestyle="--", linewidth=0.6, alpha=GRID_ALPHA)
    ax.set_axisbelow(True)


def _projeto_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _vals_tempo_s(entries: list[dict]) -> list[float]:
    vals: list[float] = []
    for e in entries:
        ts = e.get("tempo_s")
        if ts is None:
            ts = e.get("tempo")
        if ts is None:
            continue
        vals.append(float(ts))
    return vals


def _media_tempo_s(entries: list[dict]) -> float | None:
    vals = _vals_tempo_s(entries)
    if not vals:
        return None
    return sum(vals) / len(vals)


def _benchmark_lists(report: dict) -> tuple[dict[str, list], bool]:
    if "benchmark" in report and isinstance(report["benchmark"], dict):
        b = report["benchmark"]
        return (
            {
                "bfs": list(b.get("bfs") or []),
                "dfs": list(b.get("dfs") or []),
                "dijkstra": list(b.get("dijkstra") or []),
                "bellman_ford": list(b.get("bellman_ford") or []),
            },
            True,
        )
    return (
        {
            "bfs": list(report.get("bfs") or []),
            "dfs": list(report.get("dfs") or []),
            "dijkstra": list(report.get("dijkstra") or []),
            "bellman_ford": list(report.get("bellman_ford") or []),
        },
        False,
    )


def medias_benchmark(report: dict) -> dict[str, float]:
    lists, _ = _benchmark_lists(report)
    out: dict[str, float] = {}
    nomes_e_listas = [
        ("BFS", lists["bfs"]),
        ("DFS", lists["dfs"]),
        ("Dijkstra", lists["dijkstra"]),
        ("Bellman-Ford", lists["bellman_ford"]),
    ]
    for nome, lst in nomes_e_listas:
        m = _media_tempo_s(lst)
        out[nome] = m if m is not None else 0.0
    return out


def grafico_benchmark_tempos(medias: dict[str, float], saida: Path) -> None:
    ordem = ["BFS", "DFS", "Dijkstra", "Bellman-Ford"]
    vals = [max(medias[k], 1e-15) for k in ordem]
    fig, ax = plt.subplots(figsize=FIG_WIDE, constrained_layout=True)
    xpos = np.arange(len(ordem))
    bars = ax.bar(
        xpos,
        vals,
        color=COL_BENCHMARK,
        edgecolor=COLOR_EDGE_BAR,
        linewidth=0.55,
        zorder=3,
    )
    ax.set_xticks(xpos)
    ax.set_xticklabels(ordem)
    ax.set_yscale("log")
    ax.set_ylabel("Tempo médio de execução (s, escala log)")
    ax.set_xlabel("Algoritmo")
    ax.set_title(
        "Comparação de desempenho dos algoritmos\nMédia dos tempos · escala log"
    )
    ax.tick_params(axis="x", rotation=18)
    _grid_leve(ax)
    ymax = max(vals)
    for bar, v_raw in zip(bars, [medias[k] for k in ordem]):
        h = bar.get_height()
        if v_raw >= 0.001:
            lbl = f"{v_raw:.3f}"
        else:
            lbl = f"{v_raw:.1e}"
        ax.annotate(
            lbl,
            xy=(bar.get_x() + bar.get_width() / 2, h),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=FONT_LEGEND,
            fontweight="medium",
        )
    ax.set_ylim(bottom=min(vals) * 0.65, top=ymax * 2.2)
    _salvar_fig(fig, saida)
    plt.close(fig)


def grafico_distribuicao_graus(dist: dict, saida: Path) -> None:
    pares = sorted(((int(k), int(v)) for k, v in dist.items()), key=lambda x: x[0])
    graus = np.array([p[0] for p in pares], dtype=float)
    qtd = np.array([p[1] for p in pares], dtype=float)
    fig, ax = plt.subplots(figsize=FIG_WIDE, constrained_layout=True)
    ax.semilogy(
        graus,
        qtd,
        color=COL_GRAD_DIST,
        linewidth=1.5,
        linestyle="-",
        marker=None,
        alpha=0.92,
        zorder=3,
    )
    ax.set_xlabel("Grau do vértice (filme)")
    ax.set_ylabel("Número de vértices com esse grau (escala log₁₀)")
    ax.set_title(
        "Distribuição de graus na rede de filmes\nFrequências em log · cauda longa"
    )
    _grid_leve(ax)
    _salvar_fig(fig, saida)
    plt.close(fig)


def _amostra_dataframe(df: pd.DataFrame, max_pontos: int, seed: int) -> pd.DataFrame:
    if len(df) <= max_pontos:
        return df
    return df.sample(n=max_pontos, random_state=seed)


def grafico_atores_similaridade(
    edges_csv: Path,
    saida: Path,
    max_pontos: int,
) -> None:
    df = pd.read_csv(
        edges_csv,
        usecols=["actors_common", "similaridade"],
        dtype={"actors_common": int, "similaridade": float},
    )
    df = _amostra_dataframe(df, max_pontos, seed=SCATTER_SEED_ATORES)
    rng = np.random.default_rng(SCATTER_SEED_ATORES)
    jitter_x = rng.uniform(-0.32, 0.32, size=len(df))
    x_plot = df["actors_common"].astype(float).to_numpy() + jitter_x
    fig, ax = plt.subplots(figsize=FIG_SCATTER, constrained_layout=True)
    ax.scatter(
        x_plot,
        df["similaridade"],
        s=8,
        alpha=0.48,
        c=COL_SCATTER_ACTORS,
        edgecolors="none",
        rasterized=True,
    )
    ax.set_xlabel("Compartilhamento de elenco (atores em comum; leve jitter horizontal)")
    ax.set_ylabel("Similaridade entre filmes")
    ax.set_title(
        "Similaridade e elenco em comum\nNuvem com jitter horizontal"
    )
    _grid_leve(ax)
    _salvar_fig(fig, saida)
    plt.close(fig)


def grafico_similaridade_peso(
    edges_csv: Path,
    saida: Path,
    max_pontos: int,
) -> None:
    df = pd.read_csv(
        edges_csv,
        usecols=["similaridade", "peso"],
        dtype={"similaridade": float, "peso": float},
    )
    df = _amostra_dataframe(df, max_pontos, seed=SCATTER_SEED_SIM_PESO)
    xs = df["similaridade"].to_numpy()
    ys = df["peso"].to_numpy()
    fig, ax = plt.subplots(figsize=FIG_SCATTER, constrained_layout=True)
    ax.scatter(
        xs,
        ys,
        s=6,
        alpha=0.45,
        c=COL_SCATTER_SIM_PESO,
        edgecolors="none",
        rasterized=True,
    )
    # igual ao build_imdb_dataset: peso = 1/similaridade; pontos na curva esperada
    if len(xs) >= 1:
        x_min = float(np.min(xs))
        x_max = float(np.max(xs))
        if x_max > x_min * (1 + 1e-15):
            x_curve = np.linspace(x_min, x_max, 200)
        else:
            x_curve = np.array([x_min])
        y_curve = 1.0 / x_curve
        ax.plot(
            x_curve,
            y_curve,
            color=COL_CURVA_MODELO,
            linewidth=2.0,
            linestyle="-",
            alpha=0.92,
            label="Curva do modelo: peso = 1 / similaridade",
            zorder=5,
        )
        ax.legend(loc="upper right", framealpha=0.92, fontsize=FONT_LEGEND)
    ax.set_xlabel("Similaridade")
    ax.set_ylabel("Peso da aresta")
    ax.set_title(
        "Similaridade e peso das arestas\nMenor peso quando a semelhança é maior"
    )
    _grid_leve(ax)
    _salvar_fig(fig, saida)
    plt.close(fig)


def _adjacencia_nao_dirigida(edges_csv: Path) -> dict[str, set[str]]:
    df = pd.read_csv(edges_csv, usecols=["source", "target"], dtype=str)
    adj: dict[str, set[str]] = {}
    for _, row in df.iterrows():
        u, v = row["source"], row["target"]
        adj.setdefault(u, set()).add(v)
        adj.setdefault(v, set()).add(u)
    return adj


def _tamanhos_componentes_conexas(adj: dict[str, set[str]]) -> list[int]:
    visitados: set[str] = set()
    tamanhos: list[int] = []
    for inicio in adj:
        if inicio in visitados:
            continue
        pilha = [inicio]
        visitados.add(inicio)
        tam = 0
        while pilha:
            u = pilha.pop()
            tam += 1
            for w in adj[u]:
                if w not in visitados:
                    visitados.add(w)
                    pilha.append(w)
        tamanhos.append(tam)
    return tamanhos


def grafico_distribuicao_tamanhos_componentes(sizes: list[int], saida: Path) -> None:
    if not sizes:
        raise ValueError("lista de tamanhos vazia")
    sizes_ord = sorted(sizes, reverse=True)
    giant = sizes_ord[0]
    total_v = sum(sizes)
    ranks = np.arange(1, len(sizes_ord) + 1)

    fig = plt.figure(figsize=FIG_COMPS, constrained_layout=True)
    gs = fig.add_gridspec(2, 1, height_ratios=[2.1, 1.0], hspace=0.38)

    ax1 = fig.add_subplot(gs[0])
    ax1.semilogy(
        ranks,
        sizes_ord,
        color=COL_COMPS_LINE,
        linewidth=1.6,
        marker="o",
        markersize=3.8,
        markerfacecolor=COL_COMPS_MARK_FACE,
        markeredgecolor=COL_COMPS_MARK_EDGE,
        markeredgewidth=0.4,
        alpha=0.95,
        zorder=3,
    )
    ax1.set_xlabel("Ordem da componente (1 = maior, depois decrescente)")
    ax1.set_ylabel("Tamanho da componente (nº de nós), escala log₁₀")
    ax1.set_title(
        "Componentes ordenadas por tamanho\nUma gigante e muitas ilhas pequenas",
        fontsize=FONT_AXIS + 1,
    )
    _grid_leve(ax1)

    ax2 = fig.add_subplot(gs[1])
    outros_vertices = total_v - giant
    categorias = ["Demais componentes\n(soma dos tamanhos)", "Componente gigante"]
    barras_v = [outros_vertices, giant]
    y_pos = np.arange(len(categorias))
    ax2.barh(
        y_pos,
        barras_v,
        color=COL_COMPS_BAR,
        edgecolor=COLOR_EDGE_BAR,
        linewidth=0.5,
        height=0.55,
    )
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(categorias, fontsize=FONT_AXIS)
    ax2.set_xlabel("Número de vértices (filmes)")
    ax2.set_title(
        "Gigante e restante da rede\nContagem de vértices em cada grupo"
    )
    for i, v in enumerate(barras_v):
        ax2.annotate(
            f"{v:,}",
            xy=(v, i),
            xytext=(6, 0),
            textcoords="offset points",
            va="center",
            fontsize=FONT_AXIS,
            fontweight="medium",
        )
    _grid_leve(ax2)
    _salvar_fig(fig, saida)
    plt.close(fig)


def main() -> None:
    root = _projeto_root()
    parser = argparse.ArgumentParser(description="Gera PNGs a partir do report JSON e do CSV.")
    parser.add_argument(
        "--report",
        default=str(root / "out" / "parte2_report.json"),
        help="Caminho para parte2_report.json",
    )
    parser.add_argument(
        "--edges",
        default=str(root / "data" / "dataset_parte2" / "imdb_edges.csv"),
        help="CSV imdb_edges (scatters e cálculo de componentes conexas)",
    )
    parser.add_argument(
        "--out-dir",
        default=str(root / "out"),
        help="Diretório de saída das figuras",
    )
    parser.add_argument(
        "--scatter-max",
        type=int,
        default=50000,
        help="Tamanho máximo da amostra nos scatter plots (desempenho)",
    )
    args = parser.parse_args()

    report_path = Path(args.report).resolve()
    edges_path = Path(args.edges).resolve()
    out_dir = Path(args.out_dir).resolve()

    with open(report_path, encoding="utf-8") as fh:
        report = json.load(fh)

    _aplicar_estilo_relatorio()
    _, usou_benchmark = _benchmark_lists(report)
    medias = medias_benchmark(report)
    ds = report.get("dataset") or {}

    # ordem: graus, componentes, elenco x similaridade, similaridade x peso, benchmark
    dist = ds.get("distribuicao_graus")
    if not dist:
        raise KeyError('Report sem dataset["distribuicao_graus"]; rode CHECK antes.')
    grafico_distribuicao_graus(dist, out_dir / "parte2_distribuicao_graus.png")

    if not edges_path.exists():
        raise FileNotFoundError(f"CSV não encontrado: {edges_path}")
    adj = _adjacencia_nao_dirigida(edges_path)
    sizes = _tamanhos_componentes_conexas(adj)
    nv_rep = report.get("dataset", {}).get("|V|")
    nc_rep = report.get("dataset", {}).get("componentes_conexas")
    maior_rep = report.get("dataset", {}).get("maior_componente_conexa")
    print(
        "[build_visualizations] Componentes (CSV):",
        len(sizes),
        "componentes;",
        len(adj),
        "nós na adjacência;",
        "maior tamanho:",
        max(sizes) if sizes else 0,
    )
    if nc_rep is not None and len(sizes) != int(nc_rep):
        print(
            f"[build_visualizations] Aviso: report indica {nc_rep} componentes,"
            f" cálculo no CSV obteve {len(sizes)}."
        )
    if maior_rep is not None and sizes and max(sizes) != int(maior_rep):
        print(
            f"[build_visualizations] Aviso: maior componente no report={maior_rep},"
            f" no grafo do CSV={max(sizes)}."
        )

    grafico_distribuicao_tamanhos_componentes(sizes, out_dir / "parte2_componentes_conexas.png")

    grafico_atores_similaridade(
        edges_path,
        out_dir / "parte2_atores_vs_similaridade.png",
        args.scatter_max,
    )
    grafico_similaridade_peso(
        edges_path,
        out_dir / "parte2_similaridade_vs_peso.png",
        args.scatter_max,
    )

    print(
        "[build_visualizations] Tempos médios (s):",
        medias,
        "| fonte:",
        "benchmark" if usou_benchmark else "listas top-level do report",
    )
    grafico_benchmark_tempos(medias, out_dir / "parte2_benchmark_tempos.png")

    gerados = [
        "parte2_distribuicao_graus.png",
        "parte2_componentes_conexas.png",
        "parte2_atores_vs_similaridade.png",
        "parte2_similaridade_vs_peso.png",
        "parte2_benchmark_tempos.png",
    ]
    print("[build_visualizations] Figuras salvas em", out_dir)
    for nome in gerados:
        print(" ", (out_dir / nome).resolve())


if __name__ == "__main__":
    main()
