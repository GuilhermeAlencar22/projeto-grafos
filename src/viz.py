from pyvis.network import Network
import os
import matplotlib.pyplot as plt
from collections import defaultdict

def _ensure_out():
    os.makedirs("out", exist_ok=True)
def gerar_arvore_percurso(grafo, caminhos, aeroportos=None, output_path="out/arvore_percurso.html"):
    _ensure_out()
    net = Network(height="750px", width="100%", bgcolor="#020617", font_color="#e2e8f0")
    cores_rotas = ["#ef4444", "#06b6d4"]
    todos_nos = set()
    for caminho in caminhos:
        todos_nos.update(caminho)
    for node in todos_nos:
        grau = len(grafo[node])
        net.add_node(
            node,
            label=node,
            size=15 + grau * 2,
            color="#38bdf8",
            title="",
            grau=grau,
        )
    for idx, caminho in enumerate(caminhos):
        cor = cores_rotas[idx % len(cores_rotas)]
        for i in range(len(caminho) - 1):
            u, v = caminho[i], caminho[i + 1]
            net.add_edge(u, v, color=cor, width=6)
    net.set_options("""
    {
      "interaction": { "hover": true },
      "physics": {
        "solver": "repulsion",
        "repulsion": {
          "nodeDistance": 200,
          "centralGravity": 0.1,
          "springLength": 200,
          "springConstant": 0.04,
          "damping": 0.5
        },
        "stabilization": { "iterations": 150 }
      }
    }
    """)

    net.write_html(output_path)
    with open(output_path, "r+", encoding="utf-8") as f:
        html = f.read()

        nav = """
        <div style="
            position:fixed; top:0; left:0; right:0; z-index:999;
            background:#1e293b; padding:10px 20px;
            display:flex; align-items:center; gap:16px;
            border-bottom:1px solid #334155; box-shadow:0 2px 8px #0008;
        ">
            <a href="grafo_interativo.html" style="
                color:#94a3b8; text-decoration:none; font-size:13px;
                background:#0f172a; padding:6px 14px; border-radius:6px;
                border:1px solid #475569;
            ">← Voltar</a>
            <span style="color:#e2e8f0; font-weight:700; font-size:15px;">
                ⟶ Árvore de Percurso — Caminhos Mínimos
            </span>
            <div style="margin-left:auto; display:flex; gap:10px; font-size:12px;">
                <span style="color:#ef4444;">━━</span> REC → POA
                <span style="color:#06b6d4; margin-left:8px;">━━</span> MAO → GRU
            </div>
        </div>

        <div id="tt" style="
            display:none; position:fixed; z-index:1000; pointer-events:none;
            background:#1e293b; border:1px solid #475569; border-radius:10px;
            padding:12px 16px; color:#f1f5f9; font-size:13px;
            box-shadow:0 4px 20px #0009; min-width:140px; line-height:1;
        "></div>
        <script>
        document.addEventListener("mousemove", function(e){
            const tt = document.getElementById("tt");
            tt.style.left = (e.clientX + 16) + "px";
            tt.style.top  = (e.clientY + 16) + "px";
        });
        network.on("hoverNode", function(params){
            const tt   = document.getElementById("tt");
            const data = network.body.data.nodes.get(params.node);
            tt.innerHTML = `
              <div style="font-size:18px; font-weight:800; color:#f8fafc; margin-bottom:8px;
                          border-bottom:1px solid #334155; padding-bottom:6px;">
                ${data.id}
              </div>
              <table style="border-collapse:collapse;">
                <tr>
                  <td style="color:#94a3b8; padding:3px 0; padding-right:12px;">Grau</td>
                  <td style="color:#e2e8f0; font-weight:600;">${data.grau}</td>
                </tr>
              </table>
            `;
            tt.style.display = "block";
        });

        network.on("blurNode", function(){
            document.getElementById("tt").style.display = "none";
        });
        </script>
        """
        html = html.replace("</body>", nav + "</body>")
        f.seek(0)
        f.write(html)
        f.truncate()


def gerar_grafo_interativo(grafo, aeroportos, ego_metrics):
    _ensure_out()
    net = Network(height="100vh", width="100%", bgcolor="#0f172a", font_color="white")
    ego_dict = {e["aeroporto"]: e for e in ego_metrics}
    NIVEIS = {
        1: {"nos": {"GRU", "BSB", "GIG"},                          "cor": "#f43f5e", "label": "Nível 1 — Super Hubs",     "tamanho": 42},
        2: {"nos": {"CNF", "REC", "SSA", "FOR"},                   "cor": "#f97316", "label": "Nível 2 — Hubs Regionais", "tamanho": 32},
        3: {"nos": {"CWB", "POA", "FLN", "VIX", "GYN", "MAO",
                    "BEL", "CGH"},                                  "cor": "#facc15", "label": "Nível 3 — Intermediários",  "tamanho": 22},
        4: {"nos": {"NAT", "JPA", "THE"},                          "cor": "#34d399", "label": "Nível 4 — Regionais",       "tamanho": 16},
        5: {"nos": {"PVH", "RBR"},                                  "cor": "#94a3b8", "label": "Nível 5 — Periféricos",    "tamanho": 12},
    }

    def _nivel(node):
        for n, cfg in NIVEIS.items():
            if node in cfg["nos"]:
                return n
        return 5 

    graus     = {node: len(grafo[node]) for node in grafo}
    COR_ARESTA = "#1e3a5f"
    for node in grafo:
        grau      = graus[node]
        regiao    = aeroportos.get(node, {}).get("regiao", "N/A")
        ego       = ego_dict.get(node)
        densidade = round(ego["densidade_ego"], 3) if ego else 0
        nivel     = _nivel(node)
        cfg       = NIVEIS[nivel]
        net.add_node(
            node,
            label=node,
            size=cfg["tamanho"],
            color=cfg["cor"],
            borderWidth=4 if nivel <= 2 else 1,
            font={"size": 15 if nivel <= 2 else 12, "bold": nivel <= 2},
            title="",
            regiao=regiao,
            grau=grau,
            densidade=densidade,
            nivel=nivel,
            nivel_label=cfg["label"],
        )

    for u in grafo:
        for v in grafo[u]:
            if u < v:
                net.add_edge(u, v, color=COR_ARESTA, width=1, id=f"{u}_{v}")
    net.set_options("""
    {
      "interaction": { "hover": true, "tooltipDelay": 100 },
      "physics": {
        "solver": "forceAtlas2Based",
        "forceAtlas2Based": {
          "gravitationalConstant": -120,
          "centralGravity": 0.01,
          "springLength": 160,
          "springConstant": 0.06,
          "damping": 0.4,
          "avoidOverlap": 1
        },
        "stabilization": { "iterations": 300 }
      },
      "nodes": {
        "shape": "dot",
        "scaling": { "min": 14, "max": 50 }
      },
      "edges": {
        "smooth": { "type": "continuous" }
      }
    }
    """)
    net.write_html("out/grafo_interativo.html")
    with open("out/grafo_interativo.html", "r+", encoding="utf-8") as f:
        html = f.read()

        ui = """
        <div style="
            position:fixed; top:0; left:0; right:0; z-index:999;
            background:#1e293b; padding:10px 20px;
            display:flex; align-items:center; gap:16px;
            border-bottom:1px solid #334155; box-shadow:0 2px 8px #0008;
        ">
            <span style="color:#f8fafc; font-weight:700; font-size:15px; margin-right:8px;">
                ✈ Rede de Aeroportos
            </span>
            <a href="subgrafo_hubs.html" style="
                color:#f59e0b; text-decoration:none; font-size:13px;
                background:#292524; padding:6px 14px; border-radius:6px;
                border:1px solid #f59e0b;
            ">★ Subgrafo Hubs</a>
            <a href="arvore_percurso.html" style="
                color:#06b6d4; text-decoration:none; font-size:13px;
                background:#082f49; padding:6px 14px; border-radius:6px;
                border:1px solid #06b6d4;
            ">⟶ Árvore de Percurso</a>

            <div style="margin-left:auto; display:flex; gap:6px;">
                <input id="search" placeholder="Buscar aeroporto (ex: GRU)" style="
                    padding:6px 10px; border-radius:6px; border:1px solid #475569;
                    background:#0f172a; color:white; font-size:13px; width:220px;
                ">
                <button onclick="buscar()" style="
                    padding:6px 14px; border-radius:6px; border:none;
                    background:#3b82f6; color:white; cursor:pointer; font-size:13px;
                ">Buscar</button>
            </div>
        </div>
        <div style="
            position:fixed; bottom:20px; left:20px; z-index:999;
            background:#1e293b; padding:14px 18px; border-radius:10px;
            color:#e2e8f0; font-size:12px; border:1px solid #334155;
            box-shadow:0 4px 16px #0007; line-height:1;
        ">
            <div style="font-weight:700; font-size:13px; color:#f8fafc;
                        margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid #334155;">
                Hierarquia de Aeroportos
            </div>
            <div style="display:flex; flex-direction:column; gap:7px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="width:12px;height:12px;border-radius:50%;background:#f43f5e;display:inline-block;flex-shrink:0;"></span>
                    <span><b>Nível 1</b> — Super Hubs <span style="color:#64748b;">(GRU, BSB, GIG)</span></span>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="width:12px;height:12px;border-radius:50%;background:#f97316;display:inline-block;flex-shrink:0;"></span>
                    <span><b>Nível 2</b> — Hubs Regionais <span style="color:#64748b;">(CNF, REC, SSA, FOR)</span></span>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="width:12px;height:12px;border-radius:50%;background:#facc15;display:inline-block;flex-shrink:0;"></span>
                    <span><b>Nível 3</b> — Intermediários</span>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="width:12px;height:12px;border-radius:50%;background:#34d399;display:inline-block;flex-shrink:0;"></span>
                    <span><b>Nível 4</b> — Regionais <span style="color:#64748b;">(NAT, JPA, THE)</span></span>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="width:12px;height:12px;border-radius:50%;background:#94a3b8;display:inline-block;flex-shrink:0;"></span>
                    <span><b>Nível 5</b> — Periféricos <span style="color:#64748b;">(PVH, RBR)</span></span>
                </div>
            </div>
            <div style="margin-top:10px; padding-top:8px; border-top:1px solid #334155;
                        color:#64748b; font-size:11px;">
                Clique num nó para destacar conexões
            </div>
        </div>
        <div id="tt" style="
            display:none; position:fixed; z-index:1000; pointer-events:none;
            background:#1e293b; border:1px solid #475569; border-radius:10px;
            padding:12px 16px; color:#f1f5f9; font-size:13px;
            box-shadow:0 4px 20px #0009; min-width:180px; line-height:1;
        "></div>

        <script>
        document.addEventListener("DOMContentLoaded", function(){
            let canvas = document.querySelector("#mynetwork");
            if(canvas) canvas.style.marginTop = "48px";
        });

        function buscar(){
            let val = document.getElementById("search").value.trim().toUpperCase();
            if(!val) return;
            try { network.focus(val, { scale: 1.8, animation: { duration: 600 } }); }
            catch(e) { alert("Aeroporto não encontrado: " + val); }
        }
        document.getElementById("search").addEventListener("keydown", e => { if(e.key==="Enter") buscar(); });
        const tt = document.getElementById("tt");

        document.addEventListener("mousemove", function(e){
            tt.style.left = (e.clientX + 16) + "px";
            tt.style.top  = (e.clientY + 16) + "px";
        });

        network.on("hoverNode", function(params){
            const data  = network.body.data.nodes.get(params.node);
            const cor   = data.color && data.color.background ? data.color.background : data.color;
            const badge = `<span style="
                display:inline-block; margin-top:10px;
                background:${cor}22; color:${cor}; font-size:11px;
                padding:3px 10px; border-radius:20px; font-weight:700;
                border:1px solid ${cor}55;
            ">${data.nivel_label}</span>`;

            tt.innerHTML = `
              <div style="font-size:18px; font-weight:800; color:#f8fafc; margin-bottom:8px;
                          border-bottom:1px solid #334155; padding-bottom:6px;
                          display:flex; align-items:center; gap:8px;">
                <span style="width:10px;height:10px;border-radius:50%;
                             background:${cor};display:inline-block;flex-shrink:0;"></span>
                ${data.id}
              </div>
              <table style="border-collapse:collapse; width:100%;">
                <tr>
                  <td style="color:#94a3b8; padding:3px 0; padding-right:14px;">Região</td>
                  <td style="color:#e2e8f0; font-weight:600;">${data.regiao}</td>
                </tr>
                <tr>
                  <td style="color:#94a3b8; padding:3px 0; padding-right:14px;">Grau</td>
                  <td style="color:#e2e8f0; font-weight:600;">${data.grau}</td>
                </tr>
                <tr>
                  <td style="color:#94a3b8; padding:3px 0; padding-right:14px;">Densidade ego</td>
                  <td style="color:#e2e8f0; font-weight:600;">${data.densidade}</td>
                </tr>
              </table>
              ${badge}
            `;
            tt.style.display = "block";
        });

        network.on("blurNode", function(){ tt.style.display = "none"; });
        let selectedNode = null;
        const COR_NIVEL = { 1: "#f43f5e", 2: "#f97316", 3: "#facc15", 4: "#34d399", 5: "#94a3b8" };

        function resetGraph(){
            network.body.data.edges.get().forEach(edge => {
                network.body.data.edges.update({ id: edge.id, color: { color: "#1e3a5f", opacity: 1 }, width: 1 });
            });
            network.body.data.nodes.get().forEach(n => {
                network.body.data.nodes.update({ id: n.id, color: { background: COR_NIVEL[n.nivel] || "#94a3b8" } });
            });
            selectedNode = null;
        }

        network.on("click", function(params){
            if (!params.nodes || params.nodes.length === 0){ resetGraph(); return; }
            const node = params.nodes[0];
            if (selectedNode === node){ resetGraph(); return; }
            resetGraph();
            selectedNode = node;

            network.body.data.edges.get().forEach(edge => {
                const connected = edge.from === node || edge.to === node;
                network.body.data.edges.update({
                    id: edge.id,
                    color: { color: connected ? "#ef4444" : "#1e293b", opacity: connected ? 1 : 0.12 },
                    width: connected ? 3 : 1
                });
            });
            network.body.data.nodes.update({ id: node, color: { background: "#ef4444" } });
        });
        </script>
        """
        html = html.replace("</body>", ui + "</body>")

        f.seek(0)
        f.write(html)
        f.truncate()


def _estilo_base(ax, fig, titulo, subtitulo=""):
    """Aplica tema escuro consistente em todos os gráficos."""
    BG      = "#0f172a"
    PANEL   = "#1e293b"
    BORDA   = "#334155"
    TXT     = "#f1f5f9"
    TXT_DIM = "#94a3b8"

    fig.patch.set_facecolor(BG)
    ax.set_facecolor(PANEL)

    for spine in ax.spines.values():
        spine.set_edgecolor(BORDA)

    ax.tick_params(colors=TXT_DIM, labelsize=10)
    ax.xaxis.label.set_color(TXT_DIM)
    ax.yaxis.label.set_color(TXT_DIM)

    ax.set_title(titulo, color=TXT, fontsize=14, fontweight="bold", pad=16)
    if subtitulo:
        ax.set_title(
            f"{titulo}\n"
            f"$\\it{{{subtitulo}}}$",
            color=TXT, fontsize=14, fontweight="bold", pad=16,
        )

    ax.yaxis.grid(True, color=BORDA, linewidth=0.6, linestyle="--", alpha=0.7)
    ax.set_axisbelow(True)


def plot_histograma_graus(grafo):
    _ensure_out()

    NIVEIS_COR = {
        "GRU": "#f43f5e", "BSB": "#f43f5e", "GIG": "#f43f5e",
        "CNF": "#f97316", "REC": "#f97316", "SSA": "#f97316", "FOR": "#f97316",
        "CWB": "#facc15", "POA": "#facc15", "FLN": "#facc15", "VIX": "#facc15",
        "GYN": "#facc15", "MAO": "#facc15", "BEL": "#facc15", "CGH": "#facc15",
        "NAT": "#34d399", "JPA": "#34d399", "THE": "#34d399",
        "PVH": "#94a3b8", "RBR": "#94a3b8",
    }
    NIVEIS_LABEL = {
        "#f43f5e": "Super Hub",
        "#f97316": "Hub Regional",
        "#facc15": "Intermediário",
        "#34d399": "Regional",
        "#94a3b8": "Periférico",
    }

    nodes  = list(grafo.adj.keys())
    graus  = [len(grafo.adj[n]) for n in nodes]
    cores  = [NIVEIS_COR.get(n, "#94a3b8") for n in nodes]
    pares  = sorted(zip(graus, nodes, cores), reverse=True)
    graus_ord  = [g for g, _, _ in pares]
    nodes_ord  = [n for _, n, _ in pares]
    cores_ord  = [c for _, _, c in pares]

    fig, ax = plt.subplots(figsize=(13, 5))
    _estilo_base(ax, fig, "Distribuição de Graus por Aeroporto")
    bars = ax.bar(nodes_ord, graus_ord, color=cores_ord, edgecolor="#0f172a", linewidth=0.6, width=0.7)

    for bar, val in zip(bars, graus_ord):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.3,
            str(val),
            ha="center", va="bottom",
            fontsize=8.5, color="#cbd5e1", fontweight="600",
        )
    media = sum(graus_ord) / len(graus_ord)
    ax.axhline(media, color="#38bdf8", linewidth=1.2, linestyle="--", alpha=0.8)
    ax.text(
        len(nodes_ord) - 0.4, media + 0.3,
        f"Média: {media:.1f}",
        color="#38bdf8", fontsize=9, ha="right",
    )
    from matplotlib.patches import Patch
    handles = [
        Patch(facecolor=cor, label=label, edgecolor="#0f172a")
        for cor, label in NIVEIS_LABEL.items()
    ]
    ax.legend(
        handles=handles, loc="upper right",
        facecolor="#1e293b", edgecolor="#334155",
        labelcolor="#e2e8f0", fontsize=9, framealpha=1,
    )
    ax.set_xlabel("Aeroporto", labelpad=8)
    ax.set_ylabel("Grau (nº de conexões)", labelpad=8)
    ax.set_ylim(0, max(graus_ord) + 3)

    plt.tight_layout()
    plt.savefig("out/histograma.png", dpi=150, bbox_inches="tight")
    plt.close()


def plot_ranking(grafo):
    _ensure_out()

    NIVEIS_COR = {
        "GRU": "#f43f5e", "BSB": "#f43f5e", "GIG": "#f43f5e",
        "CNF": "#f97316", "REC": "#f97316", "SSA": "#f97316", "FOR": "#f97316",
        "CWB": "#facc15", "POA": "#facc15", "FLN": "#facc15", "VIX": "#facc15",
        "GYN": "#facc15", "MAO": "#facc15", "BEL": "#facc15", "CGH": "#facc15",
        "NAT": "#34d399", "JPA": "#34d399", "THE": "#34d399",
        "PVH": "#94a3b8", "RBR": "#94a3b8",
    }

    graus = {k: len(v) for k, v in grafo.adj.items()}
    top   = sorted(graus.items(), key=lambda x: x[1], reverse=True)[:10]
    labels, vals = zip(*top)
    cores = [NIVEIS_COR.get(a, "#94a3b8") for a in labels]

    fig, ax = plt.subplots(figsize=(10, 5))
    _estilo_base(ax, fig, "Top 10 Aeroportos Mais Conectados")
    bars = ax.bar(labels, vals, color=cores, edgecolor="#0f172a", linewidth=0.6, width=0.6)

    for i, (bar, val) in enumerate(zip(bars, vals)):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.2,
            str(val),
            ha="center", va="bottom",
            fontsize=10, color="#f1f5f9", fontweight="700",
        )
        if i == 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() / 2,
                "★",
                ha="center", va="center",
                fontsize=14, color="#0f172a", alpha=0.5,
            )
    ax.set_xlabel("Aeroporto", labelpad=8)
    ax.set_ylabel("Grau (nº de conexões)", labelpad=8)
    ax.set_ylim(0, max(vals) + 3)

    for i, (bar, label) in enumerate(zip(bars, labels), 1):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            -1.2,
            f"#{i}",
            ha="center", va="top",
            fontsize=8, color="#64748b",
        )
    ax.set_ylim(0, max(vals) + 3)

    plt.tight_layout()
    plt.savefig("out/ranking.png", dpi=150, bbox_inches="tight")
    plt.close()


def plot_regioes(grafo, aeroportos):
    _ensure_out()

    COR_REGIAO = {
        "Nordeste":    "#f97316",
        "Sudeste":     "#f43f5e",
        "Centro-Oeste":"#facc15",
        "Sul":         "#34d399",
        "Norte":       "#94a3b8",
    }
    soma = defaultdict(int)
    cont = defaultdict(int)
    for n in grafo:
        r = aeroportos.get(n, {}).get("regiao", "N/A")
        soma[r] += len(grafo[n])
        cont[r] += 1

    medias = sorted(
        {r: soma[r] / cont[r] for r in soma}.items(),
        key=lambda x: x[1], reverse=True,
    )
    regioes, vals = zip(*medias)
    cores = [COR_REGIAO.get(r, "#64748b") for r in regioes]
    fig, ax = plt.subplots(figsize=(8, 5))
    _estilo_base(ax, fig, "Grau Médio de Conexões por Região")
    bars = ax.bar(regioes, vals, color=cores, edgecolor="#0f172a", linewidth=0.6, width=0.55)

    for bar, val in zip(bars, vals):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.3,
            f"{val:.1f}",
            ha="center", va="bottom",
            fontsize=11, color="#f1f5f9", fontweight="700",
        )
    for i, (bar, reg) in enumerate(zip(bars, regioes)):
        n_aero = cont[reg]
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            -1.5,
            f"{n_aero} aeroporto{'s' if n_aero > 1 else ''}",
            ha="center", va="top",
            fontsize=8.5, color="#64748b",
        )

    ax.set_xlabel("Região", labelpad=20)
    ax.set_ylabel("Grau Médio", labelpad=8)
    ax.set_ylim(0, max(vals) + 3)

    plt.tight_layout()
    plt.savefig("out/regioes.png", dpi=150, bbox_inches="tight")
    plt.close()


def plot_subgrafo_hubs(grafo, aeroportos):
    _ensure_out()
    graus = {k: len(v) for k, v in grafo.adj.items()}
    hubs = sorted(graus, key=graus.get, reverse=True)[:8]
    hubs_set = set(hubs)
    max_grau = graus[hubs[0]] if hubs else 1
    net = Network(height="100vh", width="100%", bgcolor="#0f172a", font_color="white")

    for h in hubs:
        g = graus[h]
        regiao = aeroportos.get(h, {}).get("regiao", "N/A")
        # Gradiente âmbar → laranja conforme grau relativo
        intensidade = g / max_grau
        cor = "#f59e0b" if intensidade > 0.85 else ("#fb923c" if intensidade > 0.6 else "#38bdf8")
        net.add_node(
            h,
            label=h,
            size=22 + g * 1.4,
            color=cor,
            borderWidth=3,
            font={"size": 18, "bold": True},
            title="",
            regiao=regiao,
            grau=g,
        )

    for u in hubs:
        for v in grafo[u]:
            if v in hubs_set and u < v:
                peso = grafo.get_weight(u, v)
                net.add_edge(
                    u, v,
                    color="#475569",
                    width=2,
                    title=f"{u} \u2194 {v}  |  {peso}h",
                )

    net.set_options("""
    {
      "interaction": { "hover": true, "tooltipDelay": 100 },
      "physics": {
        "solver": "repulsion",
        "repulsion": {
          "nodeDistance": 220,
          "centralGravity": 0.15,
          "springLength": 180,
          "springConstant": 0.04,
          "damping": 0.5
        },
        "stabilization": { "iterations": 200 }
      },
      "edges": {
        "smooth": { "type": "curvedCW", "roundness": 0.2 }
      }
    }
    """)

    net.write_html("out/subgrafo_hubs.html")

    with open("out/subgrafo_hubs.html", "r+", encoding="utf-8") as f:
        html = f.read()

        nav = """
        <div style="
            position:fixed; top:0; left:0; right:0; z-index:999;
            background:#1e293b; padding:10px 20px;
            display:flex; align-items:center; gap:16px;
            border-bottom:1px solid #334155; box-shadow:0 2px 8px #0008;
        ">
            <a href="grafo_interativo.html" style="
                color:#94a3b8; text-decoration:none; font-size:13px;
                background:#0f172a; padding:6px 14px; border-radius:6px;
                border:1px solid #475569;
            ">← Voltar</a>
            <span style="color:#f59e0b; font-weight:700; font-size:15px;">
                ★ Subgrafo — Top 8 Hubs
            </span>
        </div>

        <div id="tt" style="
            display:none; position:fixed; z-index:1000; pointer-events:none;
            background:#1e293b; border:1px solid #475569; border-radius:10px;
            padding:12px 16px; color:#f1f5f9; font-size:13px;
            box-shadow:0 4px 20px #0009; min-width:160px; line-height:1;
        "></div>

        <script>
        document.addEventListener("mousemove", function(e){
            const tt = document.getElementById("tt");
            tt.style.left = (e.clientX + 16) + "px";
            tt.style.top  = (e.clientY + 16) + "px";
        });

        network.on("hoverNode", function(params){
            const tt   = document.getElementById("tt");
            const data = network.body.data.nodes.get(params.node);
            tt.innerHTML = `
              <div style="font-size:18px; font-weight:800; color:#f8fafc; margin-bottom:8px;
                          border-bottom:1px solid #334155; padding-bottom:6px;">
                ${data.id}
              </div>
              <table style="border-collapse:collapse; width:100%;">
                <tr>
                  <td style="color:#94a3b8; padding:3px 0; padding-right:12px;">Região</td>
                  <td style="color:#e2e8f0; font-weight:600;">${data.regiao}</td>
                </tr>
                <tr>
                  <td style="color:#94a3b8; padding:3px 0; padding-right:12px;">Grau</td>
                  <td style="color:#e2e8f0; font-weight:600;">${data.grau}</td>
                </tr>
              </table>
            `;
            tt.style.display = "block";
        });

        network.on("blurNode", function(){
            document.getElementById("tt").style.display = "none";
        });
        </script>
        """

        html = html.replace("</body>", nav + "</body>")
        f.seek(0)
        f.write(html)
        f.truncate()