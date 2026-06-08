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
FIG_WIDE    = (10.5, 5.8)
FIG_SCATTER = (9.2,  6.2)
FIG_COMPS   = (10.5, 8.2)
FIG_DPI     = 200
GRID_ALPHA  = 0.35

FONT_TITLE  = 13
FONT_AXIS   = 11
FONT_LEGEND = 9

# tema escuro — espelha parte 1 (viz.py _estilo_base)
BG      = "#0f172a"
PANEL   = "#1e293b"
BORDA   = "#334155"
TXT     = "#f1f5f9"
TXT_DIM = "#94a3b8"

COLOR_GRID     = BORDA
COLOR_EDGE_BAR = "#0f172a"

# paleta alinhada à parte 1 — hierarquia de nós e acentos primários
COL_GRAD_DIST        = "#f5c518"  # ouro — acento primário
COL_COMPS_LINE       = "#f97316"  # laranja — hub regional
COL_COMPS_MARK_FACE  = "#facc15"  # amarelo — intermediário
COL_COMPS_MARK_EDGE  = "#0f172a"  # fundo escuro para borda
COL_SCATTER_ACTORS   = "#38bdf8"  # ciano — info/média
COL_SCATTER_SIM_PESO = "#f5c518"  # ouro — acento primário
COL_CURVA_MODELO     = "#f43f5e"  # rose — super hub / destaque
COL_BENCHMARK        = ["#f43f5e", "#f97316", "#facc15", "#34d399"]  # hierarquia parte 1
COL_COMPS_BAR        = ["#94a3b8", "#f5c518"]  # periférico + ouro

SCATTER_SEED_ATORES = 42
SCATTER_SEED_SIM_PESO = 44


def _aplicar_estilo_relatorio() -> None:
    plt.rcParams.update(
        {
            "font.size": FONT_AXIS,
            "axes.titlesize": FONT_TITLE,
            "axes.labelsize": FONT_AXIS,
            "legend.fontsize": FONT_LEGEND,
            # tema escuro — espelha parte 1
            "figure.facecolor":  BG,
            "axes.facecolor":    PANEL,
            "axes.edgecolor":    BORDA,
            "axes.labelcolor":   TXT_DIM,
            "xtick.color":       TXT_DIM,
            "ytick.color":       TXT_DIM,
            "text.color":        TXT,
            "legend.facecolor":  PANEL,
            "legend.edgecolor":  BORDA,
            "grid.color":        COLOR_GRID,
            "savefig.facecolor": BG,
        }
    )


def _salvar_fig(fig: plt.Figure, path_png: Path) -> None:
    path_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path_png, dpi=FIG_DPI, bbox_inches="tight", facecolor=BG)


def _grid_leve(ax: plt.Axes) -> None:
    ax.grid(True, linestyle="--", linewidth=0.6, alpha=GRID_ALPHA, color=COLOR_GRID)
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
    complexidades = {
        "BFS":         "O(V + E)",
        "DFS":         "O(V + E)",
        "Dijkstra":    "O((V+E) log V)",
        "Bellman-Ford": "O(V · E)",
    }
    vals = [max(medias[k], 1e-15) for k in ordem]

    fig = plt.figure(figsize=(11.5, 7.0), constrained_layout=True)
    gs = fig.add_gridspec(2, 1, height_ratios=[3.0, 1.0], hspace=0.0)
    ax = fig.add_subplot(gs[0])
    ax_tab = fig.add_subplot(gs[1])

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
    ax.set_xlabel("")
    ax.set_title(
        "Comparação de desempenho dos algoritmos\n"
        "Tempo medido no grafo real IMDb (3 985 vértices, 100 000 arestas) · escala log"
    )
    ax.tick_params(axis="x", rotation=18)
    _grid_leve(ax)

    ymax = max(vals)
    for bar, v_raw in zip(bars, [medias[k] for k in ordem]):
        h = bar.get_height()
        lbl = f"{v_raw:.3f} s" if v_raw >= 0.001 else f"{v_raw:.1e} s"
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

    ax.set_ylim(bottom=min(vals) * 0.55, top=ymax * 3.5)

    # nota sobre Bellman-Ford ser executado em grafo artificial pequeno
    ax.annotate(
        "* Bellman-Ford executado em grafo\n  artificial pequeno (resultado 1e-05 s)",
        xy=(3, medias["Bellman-Ford"] if medias["Bellman-Ford"] > 1e-15 else vals[3]),
        xytext=(2.0, ymax * 1.8),
        textcoords="data",
        fontsize=FONT_LEGEND - 1,
        color=TXT_DIM,
        arrowprops=dict(arrowstyle="->", color=TXT_DIM, lw=0.8),
        ha="center",
        va="bottom",
    )

    # mini tabela de complexidade
    ax_tab.axis("off")
    col_labels = ["Algoritmo", "Complexidade teórica", "Classe"]
    classe = {
        "BFS":          "linear",
        "DFS":          "linear",
        "Dijkstra":     "quase-linear",
        "Bellman-Ford": "quadrática/cúbica",
    }
    table_data = [
        [k, complexidades[k], classe[k]]
        for k in ordem
    ]
    tbl = ax_tab.table(
        cellText=table_data,
        colLabels=col_labels,
        cellLoc="center",
        loc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(FONT_LEGEND)
    tbl.scale(1.0, 1.55)
    for (row, col), cell in tbl.get_celld().items():
        cell.set_facecolor(PANEL)
        cell.set_edgecolor(BORDA)
        cell.set_text_props(color=TXT if row > 0 else TXT_DIM)
        if row == 0:
            cell.set_facecolor(BG)
    # colorir a célula do algoritmo com a cor da barra correspondente
    for i, k in enumerate(ordem):
        tbl[(i + 1, 0)].set_facecolor(COL_BENCHMARK[i] + "44")  # mesma cor, alpha baixo

    _salvar_fig(fig, saida)
    plt.close(fig)


def grafico_distribuicao_graus(dist: dict, saida: Path) -> None:
    pares = sorted(((int(k), int(v)) for k, v in dist.items()), key=lambda x: x[0])
    graus = np.array([p[0] for p in pares], dtype=float)
    qtd = np.array([p[1] for p in pares], dtype=float)

    # grau médio fixo (calculado do dataset IMDb)
    grau_medio = 50.2

    # limiar dos top-10% hubs: grau no percentil 90 ponderado por frequência
    graus_expandidos = np.repeat(graus.astype(int), qtd.astype(int))
    limiar_hub = float(np.percentile(graus_expandidos, 90)) if len(graus_expandidos) > 0 else grau_medio

    fig, ax = plt.subplots(figsize=FIG_WIDE, constrained_layout=True)

    # área preenchida sob a curva
    ax.fill_between(
        graus,
        qtd,
        1,  # preenche até y=1 (escala log, não vai abaixo)
        color=COL_GRAD_DIST,
        alpha=0.15,
        zorder=2,
    )

    # linha principal
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

    # região sombreada dos top-10% hubs
    mask_hub = graus >= limiar_hub
    if mask_hub.any():
        ax.fill_between(
            graus[mask_hub],
            qtd[mask_hub],
            1,
            color=COL_CURVA_MODELO,
            alpha=0.22,
            zorder=2,
            label=f"Top 10% hubs (grau ≥ {int(limiar_hub)})",
        )

    # linha vertical tracejada no grau médio
    ax.axvline(
        grau_medio,
        color=COL_COMPS_MARK_FACE,
        linewidth=1.4,
        linestyle="--",
        alpha=0.85,
        zorder=4,
        label=f"Grau médio = {grau_medio}",
    )
    # anotação do grau médio
    y_annot = float(np.interp(grau_medio, graus, qtd)) if grau_medio <= graus[-1] else qtd[-1]
    ax.annotate(
        f"Grau médio\n= {grau_medio}",
        xy=(grau_medio, y_annot),
        xytext=(grau_medio + max(graus) * 0.06, y_annot * 3.5),
        textcoords="data",
        fontsize=FONT_LEGEND,
        color=COL_COMPS_MARK_FACE,
        arrowprops=dict(arrowstyle="->", color=COL_COMPS_MARK_FACE, lw=0.9),
        ha="left",
        va="center",
    )

    ax.set_xlabel("Grau do vértice (filme)")
    ax.set_ylabel("Número de vértices com esse grau (escala log₁₀)")
    ax.set_title(
        "Distribuição de graus na rede de filmes\nFrequências em log · cauda longa · top-10% hubs destacados"
    )
    ax.legend(loc="upper right", framealpha=0.85, fontsize=FONT_LEGEND)
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
        usecols=["qtd_atores_compartilhados", "similaridade"],
        dtype={"qtd_atores_compartilhados": int, "similaridade": float},
    )
    df = _amostra_dataframe(df, max_pontos, seed=SCATTER_SEED_ATORES)
    rng = np.random.default_rng(SCATTER_SEED_ATORES)
    jitter_x = rng.uniform(-0.32, 0.32, size=len(df))
    x_plot = df["qtd_atores_compartilhados"].astype(float).to_numpy() + jitter_x
    sim_arr = df["similaridade"].to_numpy()

    fig, ax = plt.subplots(figsize=FIG_SCATTER, constrained_layout=True)
    ax.scatter(
        x_plot,
        sim_arr,
        s=8,
        alpha=0.48,
        c=COL_SCATTER_ACTORS,
        edgecolors="none",
        rasterized=True,
    )

    # linhas de referência: sim = (2 * atores + generos_em_comum) / norm
    # Simplificando para mostrar bandas de 0, 1, 2 géneros em comum
    # A similaridade é: (2*atores + generos) / (total_atores + total_generos) — aprox.
    # Plotamos linhas orientativas y = offset + slope*x como referência qualitativa
    x_ref_vals = np.linspace(0, float(df["qtd_atores_compartilhados"].max()) + 0.5, 200)
    ref_lines = [
        (0, 0.00, "0 gêneros comuns"),
        (1, 0.00, "1 gênero comum"),
        (2, 0.00, "2 gêneros comuns"),
    ]
    # Normalizamos assumindo denominador típico de ~10 atores + ~3 gêneros ≈ 13
    denom_tipico = 13.0
    line_styles = ["--", "-.", ":"]
    ref_colors = ["#94a3b8", "#f97316", "#f43f5e"]
    for (gen_comuns, _offset, label), ls, rc in zip(ref_lines, line_styles, ref_colors):
        y_ref = (2.0 * x_ref_vals + gen_comuns) / denom_tipico
        mask = y_ref <= 1.05
        ax.plot(
            x_ref_vals[mask],
            y_ref[mask],
            color=rc,
            linewidth=1.1,
            linestyle=ls,
            alpha=0.75,
            label=label,
            zorder=4,
        )

    # anotação da fórmula
    ax.text(
        0.02, 0.97,
        "sim ≈ (2×atores + gêneros) / norm",
        transform=ax.transAxes,
        fontsize=FONT_LEGEND,
        color=TXT_DIM,
        va="top",
        ha="left",
        bbox=dict(facecolor=PANEL, edgecolor=BORDA, boxstyle="round,pad=0.3", alpha=0.85),
    )

    ax.set_xlabel("Atores em comum (leve jitter horizontal para legibilidade)")
    ax.set_ylabel("Similaridade entre filmes")
    ax.set_title(
        "Similaridade vs. elenco compartilhado\n"
        "Linhas guia: contribuição esperada de 0, 1 e 2 gêneros em comum"
    )
    ax.legend(loc="lower right", framealpha=0.85, fontsize=FONT_LEGEND)
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
    # usa todos os dados para o hexbin (densidade), amostra só se muito grande
    df_full = df if len(df) <= 200_000 else df.sample(n=200_000, random_state=SCATTER_SEED_SIM_PESO)
    xs = df_full["similaridade"].to_numpy()
    ys = df_full["peso"].to_numpy()

    fig, ax = plt.subplots(figsize=FIG_SCATTER, constrained_layout=True)

    # hexbin para mostrar concentração dos dados (similaridade discreta → pontos sobrepostos)
    hb = ax.hexbin(
        xs,
        ys,
        gridsize=55,
        cmap="YlOrRd",
        mincnt=1,
        linewidths=0.2,
        alpha=0.85,
        zorder=2,
        bins="log",
    )
    cbar = fig.colorbar(hb, ax=ax, pad=0.02)
    cbar.set_label("Contagem (escala log)", color=TXT_DIM, fontsize=FONT_LEGEND)
    cbar.ax.yaxis.set_tick_params(color=TXT_DIM)
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color=TXT_DIM)
    cbar.outline.set_edgecolor(BORDA)

    # curva teórica: peso = 1 / similaridade
    if len(xs) >= 1:
        x_min = float(np.min(xs))
        x_max = float(np.max(xs))
        if x_max > x_min * (1 + 1e-15):
            x_curve = np.linspace(x_min, x_max, 400)
        else:
            x_curve = np.array([x_min])
        y_curve = 1.0 / x_curve
        ax.plot(
            x_curve,
            y_curve,
            color=COL_CURVA_MODELO,
            linewidth=2.2,
            linestyle="-",
            alpha=0.95,
            label="Modelo teórico: peso = 1 / sim",
            zorder=5,
        )
        ax.legend(loc="upper right", framealpha=0.92, fontsize=FONT_LEGEND)

    ax.set_xlabel("Similaridade")
    ax.set_ylabel("Peso da aresta")
    ax.set_title(
        "Similaridade vs. peso das arestas\n"
        "Densidade hexbin — concentração real dos dados + curva teórica"
    )
    _grid_leve(ax)
    _salvar_fig(fig, saida)
    plt.close(fig)


def _adjacencia_nao_dirigida(edges_csv: Path) -> dict[str, set[str]]:
    df = pd.read_csv(edges_csv, usecols=["filme1", "filme2"], dtype=str)
    adj: dict[str, set[str]] = {}
    for _, row in df.iterrows():
        u, v = row["filme1"], row["filme2"]
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
    pct_giant = giant / total_v * 100 if total_v > 0 else 0.0
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

    # componente gigante em cima (y=1), demais em baixo (y=0)
    categorias = [
        "Demais componentes\n(soma dos tamanhos)",
        f"Componente gigante\n({pct_giant:.1f}% da rede)".replace(".", ","),
    ]
    barras_v = [outros_vertices, giant]
    # cores: COL_COMPS_BAR[0] = periférico (demais), COL_COMPS_BAR[1] = ouro (gigante)
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


def gerar_figuras_parte2(
    report_path: Path,
    edges_path: Path,
    out_dir: Path,
    scatter_max: int = 50000,
) -> list[str]:
    """gera os 5 pngs da parte 2 e devolve os nomes gerados."""
    report_path = Path(report_path).resolve()
    edges_path = Path(edges_path).resolve()
    out_dir = Path(out_dir).resolve()

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
    grafico_atores_similaridade(edges_path, out_dir / "parte2_atores_vs_similaridade.png", scatter_max)
    grafico_similaridade_peso(edges_path, out_dir / "parte2_similaridade_vs_peso.png", scatter_max)

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
    return gerados


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
        default=str(root / "data" / "dataset_parte2" / "Imdb_arestas.csv"),
        help="CSV Imdb_arestas (scatters e calculo de componentes conexas)",
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
    gerar_figuras_parte2(
        Path(args.report),
        Path(args.edges),
        Path(args.out_dir),
        scatter_max=args.scatter_max,
    )


if __name__ == "__main__":
    main()
