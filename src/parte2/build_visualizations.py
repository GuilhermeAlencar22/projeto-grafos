"""Gera os 5 PNGs de AVD da Parte 2 + subgrafo_hubs_p2.html interativo.

Uso:
    python -m src.parte2.build_visualizations
"""

from __future__ import annotations

import collections
import csv
import heapq
import json
import math
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── constantes visuais ────────────────────────────────────────────────────────
FIG_DPI = 180

BG     = "#0d1117"
PANEL  = "#0d1117"
BORDA  = "rgba(255,255,255,0.06)"
TXT    = "#ffffff"
MUTED  = (1, 1, 1, 0.45)

AMARELO = "#f5c518"
LARANJA = "#f97316"
VERMELHO= "#f43f5e"
VERDE   = "#34d399"
CIANO   = "#38bdf8"
ROXO    = "#a78bfa"

COL_BFS      = VERDE
COL_DFS      = CIANO
COL_DIJKSTRA = AMARELO
COL_BELLMAN  = LARANJA


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


MUTED_C  = (1, 1, 1, 0.45)
DIM_C    = (1, 1, 1, 0.30)
GRID_C   = (1, 1, 1, 0.07)
LEG_TXT  = (1, 1, 1, 0.70)

def _estilo() -> None:
    plt.rcParams.update({
        "font.family":       "DejaVu Sans",
        "font.size":         10,
        "text.color":        TXT,
        "axes.facecolor":    BG,
        "figure.facecolor":  BG,
        "axes.edgecolor":    "#1f2937",
        "axes.labelcolor":   MUTED_C,
        "xtick.color":       DIM_C,
        "ytick.color":       DIM_C,
        "xtick.labelsize":   9,
        "ytick.labelsize":   9,
        "grid.color":        GRID_C,
        "grid.linewidth":    0.6,
        "axes.spines.top":   False,
        "axes.spines.right": False,
        "axes.spines.left":  False,
        "axes.spines.bottom":False,
        "legend.facecolor":  BG,
        "legend.edgecolor":  "#1f2937",
        "legend.labelcolor": LEG_TXT,
        "legend.fontsize":   9,
    })


def _glow_line(ax, x, y, color, lw=2.5, label=None, **kw):
    """Plota linha com efeito glow (camada larga transparente + linha sólida)."""
    ax.plot(x, y, color=color, lw=lw * 3.5, alpha=0.18, zorder=2)
    ax.plot(x, y, color=color, lw=lw, label=label, zorder=3, **kw)


def _titulo(ax, title: str, sub: str = "") -> None:
    ax.set_title(title, color=TXT, fontsize=13, fontweight="bold", pad=10 + (12 if sub else 0))
    if sub:
        ax.text(0.5, 1.015, sub, transform=ax.transAxes,
                ha="center", va="bottom", color=MUTED_C, fontsize=9)


def _salvar(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=FIG_DPI, bbox_inches="tight",
                facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"  salvo -> {path.name}")


# ── carrega dados ─────────────────────────────────────────────────────────────

def _carregar_grafo(root: Path) -> tuple[dict[str, list], dict[str, dict]]:
    """Retorna (adj, filmes) onde adj[filme] = [(vizinho, peso, sim, atores)]."""
    filmes: dict[str, dict] = {}
    csv_f = root / "data" / "dataset_parte2" / "Imdb_filmes.csv"
    with csv_f.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            nome = (row.get("filme") or "").strip()
            if nome:
                filmes[nome] = {
                    "titulo":  nome,
                    "ano":     (row.get("ano") or "").strip(),
                    "generos": (row.get("generos") or "").strip(),
                    "nota":    (row.get("nota") or "").strip(),
                }

    adj: dict[str, list] = {f: [] for f in filmes}
    csv_a = root / "data" / "dataset_parte2" / "Imdb_arestas.csv"
    with csv_a.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            s = (row.get("filme1") or "").strip()
            t = (row.get("filme2") or "").strip()
            if not s or not t:
                continue
            try:
                peso = float(row.get("peso") or 0)
                sim  = float(row.get("similaridade") or 0)
                atores = int(float(row.get("qtd_atores_compartilhados") or 0))
            except ValueError:
                continue
            if s not in adj:
                adj[s] = []
            if t not in adj:
                adj[t] = []
            adj[s].append((t, peso, sim, atores))
            adj[t].append((s, peso, sim, atores))

    return adj, filmes


def _graus(adj: dict[str, list]) -> dict[str, int]:
    return {n: len(vizinhos) for n, vizinhos in adj.items()}


# ── algoritmos para scaling ───────────────────────────────────────────────────

def _bfs(adj: dict[str, list], origem: str) -> tuple[int, list[int]]:
    """Retorna (visitados, camadas_tamanhos)."""
    visitados = {origem}
    fila = collections.deque([origem])
    camadas: list[int] = []
    nivel = {origem: 0}
    cont_camada: dict[int, int] = {0: 1}
    while fila:
        no = fila.popleft()
        for viz, *_ in adj.get(no, []):
            if viz not in visitados:
                visitados.add(viz)
                nivel[viz] = nivel[no] + 1
                cont_camada[nivel[viz]] = cont_camada.get(nivel[viz], 0) + 1
                fila.append(viz)
    camadas = [cont_camada[i] for i in sorted(cont_camada)]
    return len(visitados), camadas


def _dfs(adj: dict[str, list], origem: str) -> int:
    visitados = set()
    pilha = [origem]
    while pilha:
        no = pilha.pop()
        if no in visitados:
            continue
        visitados.add(no)
        for viz, *_ in adj.get(no, []):
            if viz not in visitados:
                pilha.append(viz)
    return len(visitados)


def _dijkstra(adj: dict[str, list], origem: str, destino: str) -> float:
    dist = {origem: 0.0}
    heap = [(0.0, origem)]
    while heap:
        d, u = heapq.heappop(heap)
        if u == destino:
            return d
        if d > dist.get(u, math.inf):
            continue
        for v, peso, *_ in adj.get(u, []):
            nd = d + peso
            if nd < dist.get(v, math.inf):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return math.inf


def _subgrafo_induzido(adj: dict[str, list], nos: list[str]) -> dict[str, list]:
    s = set(nos)
    return {n: [(v, p, sim, a) for v, p, sim, a in adj[n] if v in s]
            for n in nos if n in adj}


def _medir_scaling(adj: dict[str, list], graus: dict[str, int],
                   tamanhos: list[int]) -> dict[str, list[float]]:
    """Mede tempo de BFS, DFS, Dijkstra em subgrafos de tamanhos crescentes."""
    nos_ordenados = sorted(graus, key=lambda x: -graus[x])
    resultados: dict[str, list[float]] = {"bfs": [], "dfs": [], "dijkstra": [], "bellman": []}

    for tam in tamanhos:
        nos_sub = nos_ordenados[:tam]
        sub = _subgrafo_induzido(adj, nos_sub)
        origem = nos_sub[0]
        destino = nos_sub[min(tam // 3, len(nos_sub) - 1)]

        t0 = time.perf_counter()
        _bfs(sub, origem)
        resultados["bfs"].append((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        _dfs(sub, origem)
        resultados["dfs"].append((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        _dijkstra(sub, origem, destino)
        resultados["dijkstra"].append((time.perf_counter() - t0) * 1000)

        # Bellman-Ford só até 500 nós (O(V·E) é lento)
        if tam <= 500:
            t0 = time.perf_counter()
            _bellman_ford_simples(sub, origem)
            resultados["bellman"].append((time.perf_counter() - t0) * 1000)
        else:
            resultados["bellman"].append(None)

    return resultados


def _bellman_ford_simples(adj: dict[str, list], origem: str) -> dict[str, float]:
    nos = list(adj.keys())
    dist = {n: math.inf for n in nos}
    dist[origem] = 0.0
    arestas = [(u, v, p) for u, vizinhos in adj.items() for v, p, *_ in vizinhos]
    for _ in range(len(nos) - 1):
        for u, v, p in arestas:
            if dist[u] + p < dist[v]:
                dist[v] = dist[u] + p
    return dist


# ── PNG 1 — histograma de graus ───────────────────────────────────────────────

def png_histograma(resumo: dict, out: Path) -> None:
    _estilo()
    dist = resumo["dataset"]["distribuicao_graus"]
    graus_vals = [int(k) for k in dist]
    counts = [dist[k] for k in dist]

    fig, ax = plt.subplots(figsize=(11, 5), facecolor=BG)
    ax.set_facecolor(BG)

    limiar_hub = 80
    cores = [AMARELO if g >= limiar_hub else CIANO for g in graus_vals]
    bars = ax.bar(graus_vals, counts, color=cores, width=1.0, linewidth=0, alpha=0.85)
    # glow nos hubs
    for bar, g in zip(bars, graus_vals):
        if g >= limiar_hub:
            bar.set_alpha(1.0)

    ax.set_xlabel("grau do filme (número de conexões)", fontsize=10)
    ax.set_ylabel("quantidade de filmes", fontsize=10)
    _titulo(ax, "Distribuição de Graus — Rede IMDb", "cauda longa: maioria dos filmes tem grau baixo, poucos concentram muitas conexões")

    patch_hub  = mpatches.Patch(color=AMARELO, label=f"hubs (grau ≥ {limiar_hub})")
    patch_norm = mpatches.Patch(color=CIANO,   label="demais filmes")
    ax.legend(handles=[patch_hub, patch_norm])
    ax.grid(axis="y", linewidth=0.5)
    ax.tick_params(length=0)
    fig.tight_layout()
    _salvar(fig, out)


# ── PNG 2 — ranking top 15 hubs ───────────────────────────────────────────────

def png_ranking_hubs(adj: dict[str, list], filmes: dict[str, dict], out: Path) -> None:
    _estilo()
    graus = _graus(adj)
    top = sorted(graus, key=lambda x: -graus[x])[:15]
    top_rev = list(reversed(top))
    vals = [graus[f] for f in top_rev]

    titulos = []
    for f in top_rev:
        t = f if len(f) <= 30 else f[:27] + "…"
        titulos.append(t)

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=BG)
    ax.set_facecolor(BG)

    cores_bar = [AMARELO if i >= len(top_rev) - 3 else CIANO for i in range(len(top_rev))]
    bars = ax.barh(range(len(top_rev)), vals, color=cores_bar, height=0.6, alpha=0.9)

    for i, (bar, v) in enumerate(zip(bars, vals)):
        ax.text(v + 0.8, bar.get_y() + bar.get_height() / 2,
                str(v), va="center", ha="left", color=TXT, fontsize=9, fontweight="bold")

    ax.set_yticks(range(len(top_rev)))
    ax.set_yticklabels(titulos, fontsize=9)
    ax.set_xlabel("grau (número de conexões)", fontsize=10)
    _titulo(ax, "Top 15 Hubs — Filmes mais conectados", "top 3 em amarelo — grau no grafo completo (3.899 filmes)")
    ax.grid(axis="x", linewidth=0.5)
    ax.tick_params(length=0)
    fig.tight_layout()
    _salvar(fig, out)


# ── PNG 3 — BFS por camadas ───────────────────────────────────────────────────

def png_bfs_camadas(adj: dict[str, list], out: Path) -> None:
    _estilo()
    fontes = ["Jurassic Park", "Forrest Gump", "Pulp Fiction"]
    cores_fontes = [AMARELO, VERDE, CIANO]

    resultados_camadas = []
    for f in fontes:
        _, camadas = _bfs(adj, f)
        resultados_camadas.append(camadas)

    max_cam = max(len(c) for c in resultados_camadas)
    for c in resultados_camadas:
        while len(c) < max_cam:
            c.append(0)

    x = np.arange(max_cam)
    n = len(fontes)
    largura = 0.25

    fig, ax = plt.subplots(figsize=(11, 5), facecolor=BG)
    ax.set_facecolor(BG)

    # linha cumulativa com glow em vez de barras
    cum_series = []
    for camadas in resultados_camadas:
        cum = []
        acc = 0
        for v in camadas:
            acc += v
            cum.append(acc)
        cum_series.append(cum)

    for fonte, cum, cor in zip(fontes, cum_series, cores_fontes):
        _glow_line(ax, range(len(cum)), cum, cor, lw=2.5, label=fonte, marker="o", markersize=5)

    ax.set_xticks(range(max_cam))
    ax.set_xticklabels([f"C{i}" for i in range(max_cam)], fontsize=9)
    ax.set_ylabel("filmes visitados (acumulado)", fontsize=10)
    _titulo(ax, "BFS — Expansão Cumulativa por Camada", "C0 = fonte  •  total: 3.899 filmes  •  mundo pequeno: 7 camadas cobrem tudo")
    ax.legend()
    ax.grid(axis="y", linewidth=0.5)
    ax.tick_params(length=0)
    fig.tight_layout()
    _salvar(fig, out)


# ── PNG 4 — benchmark horizontal ─────────────────────────────────────────────

def png_benchmark(report: dict, out: Path) -> None:
    _estilo()
    bench = report["benchmark"]

    def _media(lista: list) -> float:
        ts = [e["tempo_execucao"] for e in lista if "tempo_execucao" in e]
        return (sum(ts) / len(ts)) * 1000 if ts else 0.0

    bfs_ms      = _media(bench["bfs"])
    dfs_ms      = _media(bench["dfs"])
    dijk_ms     = _media(bench["dijkstra"])
    bf_ms       = _media(bench["bellman_ford"])  # grafo artificial pequeno

    algs   = ["BFS", "DFS", "Dijkstra", "Bellman-Ford*"]
    tempos = [bfs_ms, dfs_ms, dijk_ms, bf_ms]
    cores  = [COL_BFS, COL_DFS, COL_DIJKSTRA, COL_BELLMAN]

    fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG)
    ax.set_facecolor(BG)

    bars = ax.barh(algs, tempos, color=cores, height=0.55, alpha=0.9)
    for bar, v, cor in zip(bars, tempos, cores):
        label = f"{v:.3f} ms"
        ax.text(v + max(tempos) * 0.012, bar.get_y() + bar.get_height() / 2,
                label, va="center", ha="left", color=cor, fontsize=10, fontweight="bold")

    ax.set_xlabel("tempo médio de execução (ms)", fontsize=10)
    _titulo(ax, "Benchmark — Comparação de Desempenho",
            "* Bellman-Ford testado em grafo artificial pequeno  •  escala padronizada")
    ax.set_xlim(0, max(tempos) * 1.25)
    ax.grid(axis="x", linewidth=0.5)
    ax.tick_params(length=0)
    fig.tight_layout()
    _salvar(fig, out)


# ── PNG 5 — performance: escala ───────────────────────────────────────────────

def png_performance_escala(adj: dict[str, list], graus: dict[str, int], out: Path) -> None:
    _estilo()
    tamanhos = [100, 250, 500, 1000, 2000, 3899]
    print("  medindo scaling (pode demorar ~30s)…")
    dados = _medir_scaling(adj, graus, tamanhos)

    fig, ax = plt.subplots(figsize=(11, 5), facecolor=BG)
    ax.set_facecolor(BG)

    tam_bf = [t for t, v in zip(tamanhos, dados["bellman"]) if v is not None]
    val_bf = [v for v in dados["bellman"] if v is not None]

    _glow_line(ax, tamanhos, dados["bfs"],      COL_BFS,      lw=2.5, label="BFS",      marker="o", markersize=5)
    _glow_line(ax, tamanhos, dados["dfs"],      COL_DFS,      lw=2.5, label="DFS",      marker="s", markersize=5)
    _glow_line(ax, tamanhos, dados["dijkstra"], COL_DIJKSTRA, lw=2.5, label="Dijkstra", marker="^", markersize=5)
    if val_bf:
        _glow_line(ax, tam_bf, val_bf, COL_BELLMAN, lw=2.5, label="Bellman-Ford (até 500 nós)",
                   marker="D", markersize=5, linestyle="--")

    ax.set_xlabel("ordem do grafo (número de vértices)", fontsize=10)
    ax.set_ylabel("tempo de execução (ms)", fontsize=10)
    _titulo(ax, "Performance — Escala dos Algoritmos",
            "BF limitado a 500 nós  •  O(V·E) torna-o impraticável em grafos maiores")
    ax.legend()
    ax.grid(linewidth=0.5)
    ax.tick_params(length=0)
    fig.tight_layout()
    _salvar(fig, out)


# ── HTML interativo — subgrafo dos hubs ──────────────────────────────────────

def html_subgrafo_hubs(adj: dict[str, list], filmes: dict[str, dict], out: Path) -> None:
    graus = _graus(adj)
    top_nos = sorted(graus, key=lambda x: -graus[x])[:35]
    sub = {n: [(v, p, sim, a) for v, p, sim, a in adj[n] if v in top_nos]
           for n in top_nos}

    nodes_js, edges_js = [], []
    for i, nome in enumerate(top_nos):
        info = filmes.get(nome, {})
        g = graus[nome]
        size = 14 + int(g / 10)
        cor = "#f5c518" if i < 3 else ("#f97316" if i < 10 else "#38bdf8")
        nodes_js.append({
            "id": nome, "label": nome[:22] + ("…" if len(nome) > 22 else ""),
            "title": f"<b>{nome}</b><br>Grau: {g}<br>Gêneros: {info.get('generos','—')}<br>Ano: {info.get('ano','—')}<br>Nota: {info.get('nota','—')}",
            "size": size, "color": {"background": cor, "border": "#0f172a",
                                     "highlight": {"background": "#fff", "border": cor}},
            "font": {"color": "#f1f5f9", "size": 12},
        })

    edge_set: set[tuple] = set()
    eid = 0
    for u in top_nos:
        for v, p, sim, a in sub[u]:
            key = (min(u, v), max(u, v))
            if key not in edge_set:
                edge_set.add(key)
                w = max(0.5, min(4, sim / 5))
                edges_js.append({
                    "id": eid, "from": u, "to": v,
                    "width": w, "color": {"color": "#334155", "highlight": "#f5c518"},
                    "title": f"Sim: {sim} | Atores: {a} | Peso: {round(p,3)}",
                })
                eid += 1

    nodes_json = json.dumps(nodes_js, ensure_ascii=False)
    edges_json = json.dumps(edges_js, ensure_ascii=False)

    # caminho Dijkstra entre top 1 e top 4 para destaque
    origem_h  = top_nos[0]
    destino_h = top_nos[3]

    html = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Subgrafo dos Hubs — IMDb</title>
<script src="../interface/lib/vis-9.1.2/vis-network.min.js"></script>
<link rel="stylesheet" href="../interface/lib/vis-9.1.2/vis-network.css">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0f172a;color:#f1f5f9;font-family:"Segoe UI",sans-serif}}
#toolbar{{display:flex;align-items:center;gap:8px;flex-wrap:wrap;
  padding:12px 16px;background:#1e293b;border-bottom:1px solid #334155}}
.tb-title{{font-size:15px;font-weight:800;color:#f5c518;margin-right:8px;text-transform:uppercase;letter-spacing:.04em}}
.btn{{padding:7px 14px;border:1px solid #334155;border-radius:6px;background:#0f172a;
  color:#94a3b8;font-size:12px;font-weight:700;cursor:pointer;transition:all 140ms}}
.btn:hover{{border-color:#f5c518;color:#f5c518}}
.btn.on{{background:#f5c518;color:#0f172a;border-color:#f5c518}}
#search{{padding:7px 12px;border:1px solid #334155;border-radius:6px;background:#0f172a;
  color:#f1f5f9;font-size:12px;width:180px;outline:none}}
#search:focus{{border-color:#f5c518}}
#graph{{width:100%;height:calc(100vh - 58px)}}
#back{{margin-left:auto;font-size:12px;color:#94a3b8;text-decoration:none;padding:7px 12px;
  border:1px solid #334155;border-radius:6px}}
#back:hover{{color:#f5c518;border-color:#f5c518}}
</style>
</head>
<body>
<div id="toolbar">
  <span class="tb-title">★ Hubs IMDb</span>
  <input id="search" type="text" placeholder="Buscar filme…" oninput="buscar(this.value)">
  <button class="btn on" onclick="resetar()">Todos</button>
  <button class="btn" onclick="destacarCaminho()">Dijkstra: {origem_h[:18]}… → {destino_h[:18]}…</button>
  <a id="back" href="javascript:history.back()">← Voltar</a>
</div>
<div id="graph"></div>
<script>
const nodes = new vis.DataSet({nodes_json});
const edges = new vis.DataSet({edges_json});
const container = document.getElementById("graph");
const net = new vis.Network(container, {{nodes, edges}}, {{
  interaction: {{hover:true, tooltipDelay:80}},
  physics: {{solver:"forceAtlas2Based",
    forceAtlas2Based:{{gravitationalConstant:-180,centralGravity:0.02,
      springLength:140,springConstant:0.05,damping:0.9,avoidOverlap:0.8}},
    stabilization:{{iterations:300,fit:true}}}},
  edges: {{smooth:{{type:"continuous"}}}},
  nodes: {{shape:"dot"}}
}});

function resetar() {{
  nodes.forEach(n => nodes.update({{id:n.id, hidden:false}}));
  edges.forEach(e => edges.update({{id:e.id, color:{{color:"#334155"}}, width:e.width||1}}));
  document.querySelectorAll(".btn").forEach(b=>b.classList.remove("on"));
  document.querySelector(".btn").classList.add("on");
}}

function buscar(q) {{
  if (!q) {{ resetar(); return; }}
  q = q.toLowerCase();
  nodes.forEach(n => {{
    nodes.update({{id:n.id, hidden: !n.id.toLowerCase().includes(q)}});
  }});
}}

function destacarCaminho() {{
  const origem  = {json.dumps(origem_h)};
  const destino = {json.dumps(destino_h)};
  // Dijkstra simples no subgrafo
  const adj = {{}};
  edges.forEach(e => {{
    if (!adj[e.from]) adj[e.from] = [];
    if (!adj[e.to])   adj[e.to]   = [];
    adj[e.from].push([e.to,   e.id]);
    adj[e.to  ].push([e.from, e.id]);
  }});
  const dist = {{}}, prev = {{}}, prevEdge = {{}};
  nodes.forEach(n => dist[n.id] = Infinity);
  dist[origem] = 0;
  const pq = [[0, origem]];
  while (pq.length) {{
    pq.sort((a,b)=>a[0]-b[0]);
    const [d, u] = pq.shift();
    if (d > dist[u]) continue;
    for (const [v, eid] of (adj[u]||[])) {{
      const e = edges.get(eid);
      const nd = d + (1/(e.title?.match(/Sim: (\\d+)/)?.[1]||1));
      if (nd < dist[v]) {{ dist[v]=nd; prev[v]=u; prevEdge[v]=eid; pq.push([nd,v]); }}
    }}
  }}
  const path_edges = new Set();
  let cur = destino;
  while (prev[cur]) {{ path_edges.add(prevEdge[cur]); cur = prev[cur]; }}
  edges.forEach(e => {{
    edges.update({{id:e.id,
      color:{{color: path_edges.has(e.id) ? "#f5c518" : "#1e293b"}},
      width: path_edges.has(e.id) ? 4 : 0.5
    }});
  }});
  net.focus(origem, {{scale:1.2, animation:{{duration:600}}}});
}}
</script>
</body>
</html>"""

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"  salvo -> {out.name}")


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    root = _root()
    out_dir = root / "out" / "parte2"

    print("carregando grafo…")
    adj, filmes = _carregar_grafo(root)
    graus = _graus(adj)
    print(f"  {len(adj)} filmes, {sum(len(v) for v in adj.values())//2} arestas")

    resumo_path = root / "interface" / "data" / "resumo_parte2.json"
    resumo = json.loads(resumo_path.read_text(encoding="utf-8"))

    report_path = root / "out" / "parte2_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))

    print("\n[1/6] histograma de graus…")
    png_histograma(resumo, out_dir / "parte2_histograma_graus.png")

    print("[2/6] ranking hubs…")
    png_ranking_hubs(adj, filmes, out_dir / "parte2_ranking_hubs.png")

    print("[3/6] BFS por camadas…")
    png_bfs_camadas(adj, out_dir / "parte2_bfs_camadas.png")

    print("[4/6] benchmark horizontal…")
    png_benchmark(report, out_dir / "parte2_benchmark.png")

    print("[5/6] performance / scaling…")
    png_performance_escala(adj, graus, out_dir / "parte2_performance_escala.png")

    print("[6/6] subgrafo hubs interativo…")
    html_subgrafo_hubs(adj, filmes, root / "out" / "subgrafo_hubs_p2.html")

    print("\nTudo gerado.")


if __name__ == "__main__":
    main()
