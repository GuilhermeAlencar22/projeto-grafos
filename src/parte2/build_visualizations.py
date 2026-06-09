"""gera os pngs da narrativa AVD da parte 2 — 4 dashboards, cada um responde uma pergunta."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd

FIG_DPI    = 200
GRID_ALPHA = 0.22

FONT_TITLE  = 14
FONT_SUB    = 12
FONT_AXIS   = 10
FONT_SMALL  = 8.5
FONT_TINY   = 7.5

BG      = "#0f172a"
PANEL   = "#1e293b"
BORDA   = "#334155"
TXT     = "#f1f5f9"
TXT_DIM = "#94a3b8"

COL_PRIMARY  = "#f5c518"
COL_ORANGE   = "#f97316"
COL_RED      = "#f43f5e"
COL_GREEN    = "#34d399"
COL_CYAN     = "#38bdf8"
COL_MUTED    = "#94a3b8"
COL_PURPLE   = "#a78bfa"

COL_BFS      = COL_GREEN
COL_DFS      = COL_CYAN
COL_DIJKSTRA = COL_PRIMARY
COL_BELLMAN  = COL_ORANGE


def _estilo() -> None:
    plt.rcParams.update({
        "font.family":       "DejaVu Sans",
        "font.size":          FONT_AXIS,
        "axes.titlesize":     FONT_SUB,
        "axes.labelsize":     FONT_AXIS,
        "legend.fontsize":    FONT_SMALL,
        "figure.facecolor":   BG,
        "axes.facecolor":     PANEL,
        "axes.edgecolor":     BORDA,
        "axes.labelcolor":    TXT_DIM,
        "xtick.color":        TXT_DIM,
        "ytick.color":        TXT_DIM,
        "text.color":         TXT,
        "legend.facecolor":   PANEL,
        "legend.edgecolor":   BORDA,
        "grid.color":         BORDA,
        "savefig.facecolor":  BG,
    })


def _salvar(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=FIG_DPI, bbox_inches="tight", facecolor=BG)


def _grid(ax: plt.Axes, axis: str = "x") -> None:
    ax.grid(True, axis=axis, linestyle="--", linewidth=0.5, alpha=GRID_ALPHA, color=BORDA)
    ax.set_axisbelow(True)


def _spine(ax: plt.Axes, col: str = BORDA) -> None:
    ax.set_facecolor(PANEL)
    for sp in ax.spines.values():
        sp.set_edgecolor(col)


def _projeto_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _media(entries: list[dict]) -> float:
    vals = [float(e.get("tempo_s") or e.get("tempo") or 0)
            for e in entries if e.get("tempo_s") or e.get("tempo")]
    return sum(vals) / len(vals) if vals else 0.0


def _graus_por_filme(edges_csv: Path) -> Counter:
    df = pd.read_csv(edges_csv, usecols=["filme1", "filme2"], dtype=str)
    graus: Counter = Counter()
    for _, row in df.iterrows():
        graus[row["filme1"]] += 1
        graus[row["filme2"]] += 1
    return graus


def _adjacencia(edges_csv: Path) -> dict[str, set[str]]:
    df = pd.read_csv(edges_csv, usecols=["filme1", "filme2"], dtype=str)
    adj: dict[str, set[str]] = {}
    for _, row in df.iterrows():
        u, v = row["filme1"], row["filme2"]
        adj.setdefault(u, set()).add(v)
        adj.setdefault(v, set()).add(u)
    return adj


def _componentes(adj: dict[str, set[str]]) -> list[int]:
    visitados: set[str] = set()
    sizes: list[int] = []
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
        sizes.append(tam)
    return sizes


def _nome_curto(nome: str, maxlen: int = 20) -> str:
    n = (nome
         .replace(" (a.k.a. ID4)", "")
         .replace(", The", "")
         .replace(", A", "")
         .replace(" (Okuribito)", "")
         .replace("(Hauru no ugoku shiro)", "")
         .replace("(Sen to Chihiro no kamikakushi)", ""))
    return n[:maxlen] + "…" if len(n) > maxlen else n


# ──────────────────────────────────────────────────────────────────────────────
# GRÁFICO 1 — DASHBOARD EXPLORATÓRIO: estrutura da rede
# Pergunta: "Como é essa rede? Tem hubs? Está conectada?"
# ──────────────────────────────────────────────────────────────────────────────

def grafico_estrutura_rede(
    dist_graus: dict,
    graus: Counter,
    sizes: list[int],
    saida: Path,
) -> None:
    pares = sorted(((int(k), int(v)) for k, v in dist_graus.items()), key=lambda x: x[0])
    xs = np.array([p[0] for p in pares], dtype=float)
    ys = np.array([p[1] for p in pares], dtype=float)

    top10 = graus.most_common(10)
    nomes_top = [_nome_curto(f[0], 22) for f in top10]
    vals_top  = [f[1] for f in top10]

    giant   = max(sizes)
    total_v = sum(sizes)
    n_comp  = len(sizes)
    pct_gc  = giant / total_v * 100
    n_ilhas = total_v - giant

    grau_medio = 32.6
    xs_exp = np.repeat(xs.astype(int), ys.astype(int))
    limiar_hub = float(np.percentile(xs_exp, 90)) if len(xs_exp) > 0 else grau_medio

    fig = plt.figure(figsize=(16.0, 7.0), constrained_layout=True)
    fig.patch.set_facecolor(BG)
    fig.suptitle(
        "Dashboard Exploratório  ·  Como é a Rede IMDb?",
        fontsize=FONT_TITLE + 2, fontweight="bold", color=TXT,
    )

    gs = fig.add_gridspec(1, 3, width_ratios=[2.2, 2.0, 1.4])

    # ── painel A: distribuição de graus ──────────────────────────────────────
    ax_a = fig.add_subplot(gs[0])
    _spine(ax_a)

    ax_a.fill_between(xs, ys, 0.8, color=COL_PRIMARY, alpha=0.10, zorder=1)
    mask_hub = xs >= limiar_hub
    ax_a.fill_between(xs[mask_hub], ys[mask_hub], 0.8,
                      color=COL_RED, alpha=0.30, zorder=2, label=f"Top 10% hubs (grau ≥ {int(limiar_hub)})")
    ax_a.semilogy(xs, ys, color=COL_PRIMARY, lw=2.0, alpha=0.95, zorder=3)
    ax_a.axvline(grau_medio, color=COL_CYAN, lw=1.4, ls="--", alpha=0.85, zorder=4,
                 label=f"Grau médio = {grau_medio}")

    y_mid = float(np.interp(grau_medio, xs, ys)) if grau_medio <= xs[-1] else ys[-1]
    ax_a.annotate(f"Grau médio\n= {grau_medio}",
                  xy=(grau_medio, y_mid),
                  xytext=(grau_medio + xs[-1] * 0.10, y_mid * 5),
                  arrowprops=dict(arrowstyle="->", color=COL_CYAN, lw=1.0),
                  fontsize=FONT_TINY, color=COL_CYAN, ha="left")
    ax_a.annotate(f"Hub máximo\n= {int(xs[-1])}",
                  xy=(xs[-1], ys[-1]),
                  xytext=(xs[-1] * 0.72, ys[-1] * 7),
                  arrowprops=dict(arrowstyle="->", color=COL_RED, lw=1.0),
                  fontsize=FONT_TINY, color=COL_RED, ha="center")

    ax_a.set_xlabel("Grau do vértice (vizinhos)")
    ax_a.set_ylabel("Quantidade de filmes (escala log)")
    ax_a.set_title("A. Distribuição de Graus\nLei de potência — cauda longa", pad=10)
    ax_a.legend(loc="upper right", framealpha=0.8, fontsize=FONT_TINY)
    _grid(ax_a, "y")

    # ── painel B: top-10 hubs ────────────────────────────────────────────────
    ax_b = fig.add_subplot(gs[1])
    _spine(ax_b)

    y_pos   = np.arange(len(nomes_top))
    palette = [COL_PRIMARY if i == 0 else COL_ORANGE for i in range(len(vals_top))]
    bars = ax_b.barh(y_pos, vals_top, color=palette, edgecolor=BG, lw=0.4,
                     height=0.65, zorder=3)
    ax_b.set_yticks(y_pos)
    ax_b.set_yticklabels(nomes_top, fontsize=FONT_TINY)
    ax_b.invert_yaxis()
    for i, v in enumerate(vals_top):
        ax_b.text(v + 2, i, str(v), va="center", fontsize=FONT_TINY,
                  fontweight="bold", color=TXT)
    ax_b.set_xlabel("Grau (número de conexões diretas)")
    ax_b.set_title("B. Top 10 Hubs\nFilmes mais conectados da rede", pad=10)
    ax_b.set_xlim(0, vals_top[0] * 1.22)

    ax_b.annotate("★ Remover Royal Tenenbaums\ndesconectaria 142 filmes",
                  xy=(vals_top[0], 0),
                  xytext=(vals_top[0] * 0.55, 2.5),
                  arrowprops=dict(arrowstyle="->", color=COL_PRIMARY, lw=1.0),
                  fontsize=FONT_TINY, color=COL_PRIMARY, ha="center")
    _grid(ax_b, "x")

    # ── painel C: conectividade ──────────────────────────────────────────────
    ax_c = fig.add_subplot(gs[2])
    _spine(ax_c)

    outros = total_v - giant
    ax_c.barh(
        [0, 1],
        [outros, giant],
        color=[COL_MUTED, COL_PRIMARY],
        edgecolor=BG, lw=0.4, height=0.45, zorder=3,
    )
    ax_c.set_yticks([0, 1])
    ax_c.set_yticklabels([f"Ilhas isoladas\n({n_comp - 1} comp.)", "Componente\ngigante"],
                         fontsize=FONT_TINY)
    ax_c.text(outros + giant * 0.01, 0, f"{outros}", va="center",
              fontsize=FONT_TINY, fontweight="bold", color=TXT)
    ax_c.text(giant + giant * 0.01, 1, f"{giant:,}\n({pct_gc:.1f}%)",
              va="center", fontsize=FONT_TINY, fontweight="bold", color=TXT)
    ax_c.set_xlabel("Filmes")
    ax_c.set_xlim(0, giant * 1.30)
    ax_c.set_title("C. Conectividade\n99,6% na componente gigante", pad=10)
    _grid(ax_c, "x")

    _salvar(fig, saida)
    plt.close(fig)


# ──────────────────────────────────────────────────────────────────────────────
# GRÁFICO 2 — BFS vs DFS: comparação direta lado a lado
# Pergunta: "BFS e DFS percorrem a rede da mesma forma?"
# Resposta visual: BFS→filmes famosos, DFS→filmes obscuros (mergulho profundo)
# ──────────────────────────────────────────────────────────────────────────────

def grafico_bfs_vs_dfs(tres_fontes: dict, graus: Counter, saida: Path) -> None:
    fontes = tres_fontes.get("por_fonte", [])
    if not fontes:
        return

    # usa apenas 1 fonte para ser mais claro: Jurassic Park (mais dramático)
    fp = fontes[0]
    origem   = fp["origem"]
    bfs_nos  = fp.get("bfs", {}).get("amostra_ordem", [])[:12]
    dfs_nos  = fp.get("dfs", {}).get("amostra_ordem", [])[:12]

    # grau de cada filme no dataset (proxy de "fama")
    def grau_medio_lista(lista: list[str]) -> list[int]:
        return [graus.get(n, 1) for n in lista]

    bfs_graus = grau_medio_lista(bfs_nos)
    dfs_graus = grau_medio_lista(dfs_nos)

    # nomes curtos
    bfs_nomes = [_nome_curto(n, 18) for n in bfs_nos]
    dfs_nomes = [_nome_curto(n, 18) for n in dfs_nos]

    fig = plt.figure(figsize=(15.0, 8.0), constrained_layout=True)
    fig.patch.set_facecolor(BG)
    fig.suptitle(
        f"Dashboard Exploratório  ·  BFS vs DFS: percursos opostos a partir de '{_nome_curto(origem)}'",
        fontsize=FONT_TITLE + 1, fontweight="bold", color=TXT,
    )

    gs = fig.add_gridspec(2, 2, width_ratios=[2.8, 1.2], height_ratios=[1, 1], hspace=0.45)

    # ── painel BFS ──────────────────────────────────────────────────────────
    ax_bfs = fig.add_subplot(gs[0, 0])
    _spine(ax_bfs, col=COL_BFS)
    for sp in ax_bfs.spines.values():
        sp.set_linewidth(1.5)

    n = len(bfs_nos)
    pos = np.arange(n)
    bars = ax_bfs.barh(pos, bfs_graus, color=COL_BFS, alpha=0.85, edgecolor=BG, lw=0.4,
                       height=0.65, zorder=3)
    ax_bfs.set_yticks(pos)
    ax_bfs.set_yticklabels([f"{i+1}°  {nm}" for i, nm in enumerate(bfs_nomes)], fontsize=FONT_SMALL)
    ax_bfs.invert_yaxis()
    for i, v in enumerate(bfs_graus):
        ax_bfs.text(v + 1, i, f"grau {v}", va="center", fontsize=FONT_TINY, color=TXT_DIM)
    ax_bfs.set_xlabel("Grau do filme (conectividade na rede)")
    ax_bfs.set_title(f"BFS — percurso por camadas\n(visita os MAIS CONECTADOS primeiro)", color=COL_BFS, pad=8)
    _grid(ax_bfs, "x")

    # ── painel DFS ──────────────────────────────────────────────────────────
    ax_dfs = fig.add_subplot(gs[1, 0])
    _spine(ax_dfs, col=COL_DFS)
    for sp in ax_dfs.spines.values():
        sp.set_linewidth(1.5)

    bars2 = ax_dfs.barh(pos, dfs_graus, color=COL_DFS, alpha=0.85, edgecolor=BG, lw=0.4,
                        height=0.65, zorder=3)
    ax_dfs.set_yticks(pos)
    ax_dfs.set_yticklabels([f"{i+1}°  {nm}" for i, nm in enumerate(dfs_nomes)], fontsize=FONT_SMALL)
    ax_dfs.invert_yaxis()
    for i, v in enumerate(dfs_graus):
        ax_dfs.text(v + 1, i, f"grau {v}", va="center", fontsize=FONT_TINY, color=TXT_DIM)
    ax_dfs.set_xlabel("Grau do filme (conectividade na rede)")
    ax_dfs.set_title("DFS — percurso em profundidade\n(mergulha no 1° vizinho, chega em filmes OBSCUROS)", color=COL_DFS, pad=8)
    _grid(ax_dfs, "x")

    # ── painel explicativo ──────────────────────────────────────────────────
    ax_txt = fig.add_subplot(gs[:, 1])
    ax_txt.axis("off")
    ax_txt.set_facecolor(BG)

    # caixa de insight
    insight_linhas = [
        ("Por que são tão diferentes?", TXT, FONT_SMALL, "bold"),
        ("", TXT_DIM, FONT_TINY, "normal"),
        ("BFS usa uma FILA:", COL_BFS, FONT_SMALL, "bold"),
        ("visita todos os", TXT_DIM, FONT_TINY, "normal"),
        ("vizinhos do nível 1", TXT_DIM, FONT_TINY, "normal"),
        ("antes de avançar.", TXT_DIM, FONT_TINY, "normal"),
        ("→ 1° camada: famosos", TXT_DIM, FONT_TINY, "normal"),
        ("", TXT_DIM, FONT_TINY, "normal"),
        ("DFS usa uma PILHA:", COL_DFS, FONT_SMALL, "bold"),
        ("mergulha pelo 1°", TXT_DIM, FONT_TINY, "normal"),
        ("vizinho até o fim", TXT_DIM, FONT_TINY, "normal"),
        ("antes de voltar.", TXT_DIM, FONT_TINY, "normal"),
        ("→ 1° camada: obscuros", TXT_DIM, FONT_TINY, "normal"),
        ("", TXT_DIM, FONT_TINY, "normal"),
        ("Resultado final:", TXT, FONT_SMALL, "bold"),
        ("Ambos visitam", TXT_DIM, FONT_TINY, "normal"),
        ("os mesmos 3.899", TXT_DIM, FONT_TINY, "normal"),
        ("filmes. Apenas", TXT_DIM, FONT_TINY, "normal"),
        ("a ORDEM muda.", TXT_DIM, FONT_TINY, "normal"),
        ("", TXT_DIM, FONT_TINY, "normal"),
        ("BFS ideal para:", TXT, FONT_SMALL, "bold"),
        ("menor nº de saltos", COL_BFS, FONT_TINY, "normal"),
        ("entre filmes", COL_BFS, FONT_TINY, "normal"),
        ("", TXT_DIM, FONT_TINY, "normal"),
        ("DFS ideal para:", TXT, FONT_SMALL, "bold"),
        ("detectar ciclos", COL_DFS, FONT_TINY, "normal"),
        ("exploração profunda", COL_DFS, FONT_TINY, "normal"),
    ]

    y = 0.98
    for (texto, cor, fsize, fw) in insight_linhas:
        ax_txt.text(0.10, y, texto, transform=ax_txt.transAxes,
                    va="top", ha="left", fontsize=fsize,
                    color=cor, fontweight=fw, linespacing=1.4)
        y -= 0.033 if texto else 0.018

    bfs_p = mpatches.Patch(color=COL_BFS, label="BFS — por camadas")
    dfs_p = mpatches.Patch(color=COL_DFS, label="DFS — em profundidade")
    fig.legend(handles=[bfs_p, dfs_p], loc="lower center", ncol=2,
               framealpha=0.8, fontsize=FONT_SMALL, bbox_to_anchor=(0.42, -0.01))

    _salvar(fig, saida)
    plt.close(fig)


# ──────────────────────────────────────────────────────────────────────────────
# GRÁFICO 3 — DIJKSTRA: caminho mínimo com contexto
# Pergunta: "O Dijkstra realmente escolhe os filmes mais parecidos?"
# ──────────────────────────────────────────────────────────────────────────────

def grafico_caminho_dijkstra(dijkstra_entries: list[dict], saida: Path) -> None:
    validos = [e for e in dijkstra_entries if e.get("caminho") and len(e["caminho"]) >= 2]
    if not validos:
        return

    entry_longo = max(validos, key=lambda e: e.get("tamanho_caminho", 0))
    entry_curto = min(validos, key=lambda e: e.get("custo_total", 999))

    fig = plt.figure(figsize=(15.0, 8.5), constrained_layout=True)
    fig.patch.set_facecolor(BG)
    fig.suptitle(
        "Dashboard Explanatório  ·  Dijkstra: o caminho pelo elenco mais parecido",
        fontsize=FONT_TITLE + 2, fontweight="bold", color=TXT,
    )

    gs = fig.add_gridspec(2, 2, width_ratios=[3.2, 1.0], height_ratios=[1.6, 1.0])

    def _desenhar_caminho(ax: plt.Axes, entry: dict, titulo: str, cor_titulo: str) -> None:
        caminho = entry["caminho"]
        custo   = entry.get("custo_total") or 0.0
        n = len(caminho)
        ax.set_xlim(-0.7, n - 0.3)
        ax.set_ylim(-0.65, 0.65)
        ax.axis("off")
        ax.set_facecolor(BG)
        ax.set_title(titulo, fontsize=FONT_AXIS, color=cor_titulo, pad=8, fontweight="bold")

        radius = 0.17
        for i, filme in enumerate(caminho):
            is_orig = i == 0
            is_dest = i == n - 1
            cor = COL_RED if is_orig else (COL_GREEN if is_dest else COL_PRIMARY)

            circle = plt.Circle((i, 0), radius, color=cor, zorder=4, lw=0)
            ax.add_patch(circle)

            nc = _nome_curto(filme, 14)
            partes = nc.split()
            if len(nc) > 12 and len(partes) > 1:
                mid = max(1, len(partes) // 2)
                nc = " ".join(partes[:mid]) + "\n" + " ".join(partes[mid:])

            ax.text(i, -radius - 0.06, nc,
                    ha="center", va="top", fontsize=6.5, color=TXT, zorder=5)

            if i < n - 1:
                ax.annotate("",
                    xy=(i + 1 - radius - 0.02, 0),
                    xytext=(i + radius + 0.02, 0),
                    arrowprops=dict(arrowstyle="-|>", color=COL_ORANGE, lw=1.8),
                    zorder=3)

        ax.text(0,     radius + 0.09, "ORIGEM",  ha="center", va="bottom",
                fontsize=FONT_TINY, fontweight="bold", color=COL_RED)
        ax.text(n - 1, radius + 0.09, "DESTINO", ha="center", va="bottom",
                fontsize=FONT_TINY, fontweight="bold", color=COL_GREEN)

        ax.text(0.5, -0.58, f"Custo total: {custo:.3f}  ·  {n} filmes no caminho",
                transform=ax.transAxes, ha="center", fontsize=FONT_SMALL, color=TXT_DIM,
                bbox=dict(facecolor=PANEL, edgecolor=BORDA, boxstyle="round,pad=0.3"))

    ax_l = fig.add_subplot(gs[0, 0])
    _desenhar_caminho(ax_l, entry_longo,
                      f"Caminho mais longo — {_nome_curto(entry_longo['origem'])} → {_nome_curto(entry_longo['destino'])}",
                      COL_PRIMARY)

    ax_c = fig.add_subplot(gs[1, 0])
    _desenhar_caminho(ax_c, entry_curto,
                      f"Maior similaridade — {_nome_curto(entry_curto['origem'])} → {_nome_curto(entry_curto['destino'])}",
                      COL_GREEN)

    # ── painel de insight ────────────────────────────────────────────────────
    ax_i = fig.add_subplot(gs[:, 1])
    ax_i.axis("off")

    linhas = [
        ("Como funciona?", TXT, FONT_SMALL, "bold"),
        ("", "", 0, "normal"),
        ("peso = 1 / sim", COL_PRIMARY, FONT_SMALL, "bold"),
        ("", "", 0, "normal"),
        ("Mais parecidos", TXT_DIM, FONT_TINY, "normal"),
        ("= menor peso", TXT_DIM, FONT_TINY, "normal"),
        ("= caminho mais", TXT_DIM, FONT_TINY, "normal"),
        ("barato.", TXT_DIM, FONT_TINY, "normal"),
        ("", "", 0, "normal"),
        ("Departures → Bad Taste", TXT, FONT_TINY, "bold"),
        ("gêneros opostos", TXT_DIM, FONT_TINY, "normal"),
        ("13 filmes, custo 3.29", COL_ORANGE, FONT_TINY, "normal"),
        ("", "", 0, "normal"),
        ("Caminho similar:", TXT, FONT_TINY, "bold"),
        ("elenco direto", TXT_DIM, FONT_TINY, "normal"),
        (f"custo {entry_curto.get('custo_total', 0):.3f}", COL_GREEN, FONT_TINY, "normal"),
        ("", "", 0, "normal"),
        ("Gestalt:", TXT, FONT_SMALL, "bold"),
        ("Vermelho = origem", COL_RED, FONT_TINY, "normal"),
        ("Verde = destino", COL_GREEN, FONT_TINY, "normal"),
        ("Dourado = via", COL_PRIMARY, FONT_TINY, "normal"),
        ("Seta = aresta real", TXT_DIM, FONT_TINY, "normal"),
    ]

    y = 0.96
    for (texto, cor, fsize, fw) in linhas:
        if texto:
            ax_i.text(0.08, y, texto, transform=ax_i.transAxes,
                      va="top", ha="left", fontsize=fsize,
                      color=cor, fontweight=fw)
        y -= 0.038 if texto else 0.016

    orig_p = mpatches.Patch(color=COL_RED,     label="Origem")
    dest_p = mpatches.Patch(color=COL_GREEN,   label="Destino")
    mid_p  = mpatches.Patch(color=COL_PRIMARY, label="Intermediário")
    fig.legend(handles=[orig_p, dest_p, mid_p],
               loc="lower center", ncol=3, framealpha=0.8,
               fontsize=FONT_SMALL, bbox_to_anchor=(0.44, -0.02))

    _salvar(fig, saida)
    plt.close(fig)


# ──────────────────────────────────────────────────────────────────────────────
# GRÁFICO 4 — HEATMAP DE COMPARAÇÃO + BENCHMARK
# Pergunta: "Qual algoritmo usar em cada situação?"
# ──────────────────────────────────────────────────────────────────────────────

def grafico_heatmap_performance(medias: dict[str, float], saida: Path) -> None:
    algos    = ["BFS", "DFS", "Dijkstra", "Bellman-Ford"]
    cores    = [COL_BFS, COL_DFS, COL_DIJKSTRA, COL_BELLMAN]

    metricas = [
        "Velocidade\nde execução",
        "Caminho\nmínimo (saltos)",
        "Caminho\nponderado",
        "Suporta\npesos negativos",
        "Detecta ciclos\nnegativos",
    ]

    scores = np.array([
        [10,  9,  1,  1,  1],
        [ 9,  9,  1,  1,  9],
        [ 7,  8, 10,  1,  1],
        [ 1,  1,  7, 10, 10],
    ], dtype=float)

    labels_cell = [
        ["8 ms",     "Sim",    "Não",    "Não",     "Não"],
        ["11 ms",    "Sim",    "Não",    "Não",     "Sim"],
        ["20 ms",    "Sim",    "Sim",    "Não",     "Não"],
        ["µs (art.)","Parcial","Sim",    "Sim",     "Sim"],
    ]

    fig = plt.figure(figsize=(14.0, 7.0), constrained_layout=True)
    fig.patch.set_facecolor(BG)
    fig.suptitle(
        "Dashboard Comparativo  ·  Qual algoritmo usar em cada situação?",
        fontsize=FONT_TITLE + 2, fontweight="bold", color=TXT,
    )

    gs = fig.add_gridspec(1, 2, width_ratios=[1.7, 1.0])

    # ── heatmap de adequação ─────────────────────────────────────────────────
    ax_h = fig.add_subplot(gs[0])
    _spine(ax_h)

    cmap = plt.cm.RdYlGn
    im = ax_h.imshow(scores, cmap=cmap, vmin=0, vmax=10,
                     aspect="auto", interpolation="nearest", alpha=0.88)

    ax_h.set_xticks(range(len(metricas)))
    ax_h.set_xticklabels(metricas, fontsize=FONT_TINY, color=TXT)
    ax_h.set_yticks(range(len(algos)))
    ax_h.set_yticklabels(algos, fontsize=FONT_AXIS, color=TXT, fontweight="bold")
    ax_h.tick_params(length=0)

    # colore os labels dos algoritmos com as cores deles
    for i, cor in enumerate(cores):
        ax_h.get_yticklabels()[i].set_color(cor)

    for i in range(len(algos)):
        for j in range(len(metricas)):
            s = scores[i, j]
            txt_col = "black" if 3 < s < 8 else "white"
            ax_h.text(j, i, labels_cell[i][j],
                      ha="center", va="center", fontsize=FONT_SMALL,
                      color=txt_col, fontweight="bold")

    cbar = fig.colorbar(im, ax=ax_h, pad=0.01, shrink=0.80, aspect=30)
    cbar.set_label("Adequação para a tarefa (0 = ruim · 10 = ideal)",
                   color=TXT_DIM, fontsize=FONT_TINY)
    cbar.ax.yaxis.set_tick_params(color=TXT_DIM)
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color=TXT_DIM, fontsize=FONT_TINY)
    cbar.outline.set_edgecolor(BORDA)

    ax_h.set_title("Mapa de Adequação por Critério\nVerde = melhor opção · Vermelho = limitação", pad=10)

    # ── benchmark ────────────────────────────────────────────────────────────
    ax_b = fig.add_subplot(gs[1])
    _spine(ax_b)

    tempos = [max(medias.get(k, 1e-9), 1e-9) for k in algos]
    y_pos = np.arange(len(algos))
    bars = ax_b.barh(y_pos, tempos, color=cores, edgecolor=BG, lw=0.4,
                     height=0.55, zorder=3)
    ax_b.set_xscale("log")
    ax_b.set_yticks(y_pos)
    ax_b.set_yticklabels(algos, fontsize=FONT_AXIS, fontweight="bold")
    for i, lbl in enumerate(ax_b.get_yticklabels()):
        lbl.set_color(cores[i])
    ax_b.set_xlabel("Tempo médio de execução (escala log)", fontsize=FONT_TINY)
    ax_b.set_title("Benchmark Real — Grafo IMDb\n(escala log — ordens de grandeza diferentes)", pad=10)

    complexidades = ["O(V+E)", "O(V+E)", "O((V+E)logV)", "O(V·E)*"]
    for bar, v, comp in zip(bars, tempos, complexidades):
        lbl = f"{v*1000:.1f} ms" if v >= 0.001 else f"{v*1e6:.1f} µs"
        ax_b.text(bar.get_width() * 1.4, bar.get_y() + bar.get_height() / 2,
                  f"{lbl}  {comp}", va="center", fontsize=FONT_TINY, color=TXT)

    ax_b.annotate("* testado em grafo\nartificial (pesos neg.)",
                  xy=(tempos[3], 3), xytext=(tempos[3] * 10, 3.4),
                  fontsize=6.5, color=TXT_DIM,
                  arrowprops=dict(arrowstyle="->", color=TXT_DIM, lw=0.7))

    _grid(ax_b, "x")
    _salvar(fig, saida)
    plt.close(fig)


# ──────────────────────────────────────────────────────────────────────────────
# ORQUESTRADOR
# ──────────────────────────────────────────────────────────────────────────────

def gerar_figuras_parte2(
    report_path: Path,
    edges_path: Path,
    out_dir: Path,
    scatter_max: int = 50000,
) -> list[str]:
    report_path = Path(report_path).resolve()
    edges_path  = Path(edges_path).resolve()
    out_dir     = Path(out_dir).resolve()

    with open(report_path, encoding="utf-8") as fh:
        report = json.load(fh)

    _estilo()

    ds = report.get("dataset") or {}
    dist = ds.get("distribuicao_graus")
    if not dist:
        raise KeyError('Report sem dataset["distribuicao_graus"]')
    if not edges_path.exists():
        raise FileNotFoundError(f"CSV não encontrado: {edges_path}")

    graus = _graus_por_filme(edges_path)
    adj   = _adjacencia(edges_path)
    sizes = _componentes(adj)

    bench = report.get("benchmark", {})
    if isinstance(bench, dict) and "bfs" in bench:
        medias_b = {
            "BFS":          _media(bench.get("bfs", [])),
            "DFS":          _media(bench.get("dfs", [])),
            "Dijkstra":     _media(bench.get("dijkstra", [])),
            "Bellman-Ford": _media(bench.get("bellman_ford", [])),
        }
    else:
        medias_b = {
            "BFS":          _media(report.get("bfs", [])),
            "DFS":          _media(report.get("dfs", [])),
            "Dijkstra":     _media(report.get("dijkstra", [])),
            "Bellman-Ford": _media(report.get("bellman_ford", [])),
        }

    tres_fontes = report.get("tres_fontes", {})
    dij_entries = report.get("dijkstra", [])

    grafico_estrutura_rede(dist, graus, sizes,
                           out_dir / "parte2_estrutura_rede.png")
    grafico_bfs_vs_dfs(tres_fontes, graus,
                       out_dir / "parte2_heatmap_bfs_dfs.png")
    grafico_caminho_dijkstra(dij_entries,
                             out_dir / "parte2_caminho_dijkstra.png")
    grafico_heatmap_performance(medias_b,
                                out_dir / "parte2_heatmap_performance.png")

    gerados = [
        "parte2_estrutura_rede.png",
        "parte2_heatmap_bfs_dfs.png",
        "parte2_caminho_dijkstra.png",
        "parte2_heatmap_performance.png",
    ]
    print("[build_visualizations] Figuras salvas em", out_dir)
    for nome in gerados:
        print(" ", (out_dir / nome).resolve())
    return gerados


def main() -> None:
    root = _projeto_root()
    parser = argparse.ArgumentParser(description="Gera PNGs AVD da parte 2.")
    parser.add_argument("--report",      default=str(root / "out" / "parte2_report.json"))
    parser.add_argument("--edges",       default=str(root / "data" / "dataset_parte2" / "Imdb_arestas.csv"))
    parser.add_argument("--out-dir",     default=str(root / "out" / "parte2"))
    parser.add_argument("--scatter-max", type=int, default=50000)
    args = parser.parse_args()
    gerar_figuras_parte2(Path(args.report), Path(args.edges), Path(args.out_dir), args.scatter_max)


if __name__ == "__main__":
    main()
