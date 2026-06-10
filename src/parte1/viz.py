"""visualizações da parte 1: grafo interativo, árvore de percurso, subgrafo e gráficos."""

import argparse
import csv
import json
import os
import shutil
import sys
from pathlib import Path
from collections import defaultdict

def _ensure_out():
    os.makedirs("out", exist_ok=True)


def _matplotlib_pyplot():
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    return plt


def gerar_arvore_percurso(grafo, caminhos, aeroportos=None, output_path="out/arvore_percurso.html"):
    from pyvis.network import Network

    _ensure_out()
    net = Network(height="750px", width="100%", bgcolor="#020617", font_color="#e2e8f0")
    cores_rotas = ["#ef4444", "#06b6d4"]
    todos_nos = set()
    for caminho in caminhos:
        todos_nos.update(caminho)
    for node in todos_nos:
        grau = len(grafo[node])
        info = (aeroportos or {}).get(node, {})
        cidade = info.get("cidade", node)
        regiao = info.get("regiao", "N/A")
        COR_NO = {
            "Norte": {"background": "#1e3a5f", "border": "#60a5fa"},
            "Nordeste": {"background": "#431407", "border": "#f97316"},
            "Sudeste": {"background": "#4c0519", "border": "#f43f5e"},
            "Sul": {"background": "#052e16", "border": "#4ade80"},
            "Centro-Oeste": {"background": "#422006", "border": "#facc15"},
        }
        cor = COR_NO.get(regiao, {"background": "#1e293b", "border": "#38bdf8"})
        net.add_node(
            node,
            label=node,
            size=15 + grau * 2,
            color={"border": cor["border"], "background": cor["background"], "highlight": {"border": "#facc15", "background": cor["background"]}},
            borderWidth=3,
            title="",
            grau=grau,
            cidade=cidade,
            regiao=regiao,
        )
    for idx, caminho in enumerate(caminhos):
        cor = cores_rotas[idx % len(cores_rotas)]
        for i in range(len(caminho) - 1):
            u, v = caminho[i], caminho[i + 1]
            peso = grafo.get_weight(u, v)
            net.add_edge(u, v, color=cor, width=6, id=f"rota{idx}_{u}_{v}", rota_idx=idx, peso=peso)
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

        rotas_percurso = [
            {
                "label": f"{caminho[0]} → {caminho[-1]}",
                "nodes": caminho,
                "edges": [f"rota{idx}_{caminho[i]}_{caminho[i + 1]}" for i in range(len(caminho) - 1)],
            }
            for idx, caminho in enumerate(caminhos)
        ]
        botoes_rotas = "".join(
            f"""<button class="percurso-tab{' active' if idx == 0 else ''}" onclick="selecionarArvorePercurso({idx})">{rota['label']}</button>"""
            for idx, rota in enumerate(rotas_percurso)
        )
        rotas_json = json.dumps(rotas_percurso, ensure_ascii=False)

        nav = """<div style="position:fixed; top:0; left:0; right:0; z-index:999; background:#1e293b; padding:14px 24px; display:flex; align-items:center; gap:14px; border-bottom:1px solid #334155; box-shadow:0 2px 8px #0008;">
            <a href="#" onclick="history.back();return false;" style="color:#94a3b8; text-decoration:none; font-size:14px; background:#0f172a; padding:7px 14px; border-radius:6px; border:1px solid #475569;">&#8592; Voltar</a>
            <span style="color:#f8fafc; font-weight:700; font-size:18px;">Arvores de Percurso</span>
            <div style="display:flex; gap:8px; flex-wrap:wrap;">
                __BOTOES_ROTAS__
            </div>
            <style>
                .percurso-tab{background:#0f172a;color:#94a3b8;border:1px solid #475569;border-radius:6px;padding:7px 14px;font-size:14px;font-weight:700;cursor:pointer;font-family:inherit;text-decoration:none;}
                .percurso-tab:hover{color:#e2e8f0;border-color:#94a3b8;}
                .percurso-tab.active{background:#292524;color:#facc15;border-color:#facc15;}
            </style>
        </div>
        <div id="tt" style="
            display:none; position:fixed; z-index:1000; pointer-events:none;
            background:#1e293b; border:1px solid #475569; border-radius:10px;
            padding:12px 16px; color:#f1f5f9; font-size:13px;
            box-shadow:0 4px 20px #0009; min-width:140px; line-height:1;
        "></div>
        <script>
        const ROTAS_PERCURSO = __ROTAS_PERCURSO__;

        document.addEventListener("mousemove", function(e){
            const tt = document.getElementById("tt");
            tt.style.left = (e.clientX + 16) + "px";
            tt.style.top  = (e.clientY + 16) + "px";
        });

        function selecionarArvorePercurso(idx){
            const rota = ROTAS_PERCURSO[idx];
            if(!rota) return;
            const rotaNodes = new Set(rota.nodes);
            const rotaEdges = new Set(rota.edges);

            network.body.data.nodes.get().forEach((node) => {
                network.body.data.nodes.update({
                    id: node.id,
                    hidden: !rotaNodes.has(node.id)
                });
            });
            network.body.data.edges.get().forEach((edge) => {
                const ativo = rotaEdges.has(edge.id);
                network.body.data.edges.update({
                    id: edge.id,
                    hidden: !ativo,
                    width: ativo ? 6 : 1
                });
            });
            document.querySelectorAll(".percurso-tab").forEach((btn) => btn.classList.remove("active"));
            const btn = document.querySelectorAll(".percurso-tab")[idx];
            if(btn) btn.classList.add("active");
            try { network.fit({ nodes: rota.nodes, animation: { duration: 450 } }); } catch(_) {}
        }

        function hToStr(h){
            if(h === null || h === undefined || isNaN(h)) return "—";
            const horas = Math.floor(h);
            const mins  = Math.round((h - horas) * 60);
            return horas > 0 ? (mins > 0 ? horas+"h "+mins+"min" : horas+"h") : mins+"min";
        }

        network.on("hoverNode", function(params){
            const tt   = document.getElementById("tt");
            const data = network.body.data.nodes.get(params.node);
            tt.innerHTML = `
              <div style="font-size:18px; font-weight:800; color:#38bdf8; margin-bottom:8px;
                          border-bottom:1px solid #334155; padding-bottom:6px;">
                ${data.id} <span style="color:#94a3b8; font-size:13px; font-weight:400;">${data.cidade || ""}</span>
              </div>
              <table style="border-collapse:collapse; width:100%;">
                <tr>
                  <td style="color:#94a3b8; padding:3px 0; padding-right:12px;">Região</td>
                  <td style="color:#e2e8f0; font-weight:600;">${data.regiao || "N/A"}</td>
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

        network.on("hoverEdge", function(params){
            const tt   = document.getElementById("tt");
            const edge = network.body.data.edges.get(params.edge);
            if(!edge) return;
            const peso = edge.peso != null ? Number(edge.peso) : null;
            tt.innerHTML = `
              <div style="font-size:15px; font-weight:800; color:#f8fafc; margin-bottom:8px;
                          border-bottom:1px solid #334155; padding-bottom:6px;
                          display:flex; align-items:center; gap:8px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#facc15" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                ${edge.from} — ${edge.to}
              </div>
              <table style="border-collapse:collapse; width:100%;">
                <tr>
                  <td style="color:#94a3b8; padding:3px 0; padding-right:12px;">Custo</td>
                  <td style="color:#facc15; font-weight:700;">${peso !== null ? peso.toFixed(2) : "N/A"}</td>
                </tr>
                <tr>
                  <td style="color:#94a3b8; padding:3px 0; padding-right:12px;">Tempo real</td>
                  <td style="color:#e2e8f0; font-weight:600;">${hToStr(peso)}</td>
                </tr>
              </table>
            `;
            tt.style.display = "block";
        });

        network.on("blurEdge", function(){
            document.getElementById("tt").style.display = "none";
        });

        setTimeout(() => selecionarArvorePercurso(0), 250);
        </script>
        """.replace("__BOTOES_ROTAS__", botoes_rotas).replace("__ROTAS_PERCURSO__", rotas_json)
        html = html.replace("</body>", nav + "</body>")
        f.seek(0)
        f.write(html)
        f.truncate()


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REPORT_PARTE2 = ROOT / "out" / "parte2_report.json"
EDGES_PARTE2 = ROOT / "data" / "dataset_parte2" / "Imdb_arestas.csv"
OUT_PARTE2 = ROOT / "out" / "parte2"
INTERFACE_ASSETS = ROOT / "interface" / "assets"


def _rodar_parte2(args):
    from src.parte2.build_visualizations import gerar_figuras_parte2

    out_dir = Path(args.out_dir)
    gerados = gerar_figuras_parte2(
        report_path=Path(args.report),
        edges_path=Path(args.edges),
        out_dir=out_dir,
        scatter_max=args.scatter_max,
    )

    if args.mirror_interface:
        INTERFACE_ASSETS.mkdir(parents=True, exist_ok=True)
        for nome in gerados:
            shutil.copyfile(out_dir / nome, INTERFACE_ASSETS / nome)
        print(f"[viz] espelhado em {INTERFACE_ASSETS}")


def main():
    parser = argparse.ArgumentParser(description="gera visualizacoes do projeto.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p2 = sub.add_parser("parte2", help="figuras da parte 2.")
    p2.add_argument("--report", default=str(REPORT_PARTE2))
    p2.add_argument("--edges", default=str(EDGES_PARTE2))
    p2.add_argument("--out-dir", default=str(OUT_PARTE2))
    p2.add_argument("--scatter-max", type=int, default=50000)
    p2.add_argument(
        "--no-mirror",
        dest="mirror_interface",
        action="store_false",
        help="nao copia os pngs pra interface/assets.",
    )
    p2.set_defaults(func=_rodar_parte2, mirror_interface=True)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

def gerar_grafo_interativo(grafo, aeroportos, ego_metrics):
    from pyvis.network import Network

    _ensure_out()
    net = Network(height="100vh", width="100%", bgcolor="#0f172a", font_color="white")
    ego_dict = {e["aeroporto"]: e for e in ego_metrics}
    arestas_info = {}
    adj_path = Path("data/adjacencias_aeroportos.csv")
    if adj_path.exists():
        with adj_path.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                origem = row.get("origem", "").strip()
                destino = row.get("destino", "").strip()
                if not origem or not destino:
                    continue
                chave = tuple(sorted((origem, destino)))
                arestas_info[chave] = {
                    "tipo": row.get("tipo_conexao", "").strip() or "N/A",
                    "justificativa": row.get("justificativa", "").strip() or "N/A",
                    "peso": row.get("peso", "").strip() or "N/A",
                }
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
        info_aero = aeroportos.get(node, {})
        regiao    = info_aero.get("regiao", "N/A")
        cidade    = info_aero.get("cidade", node)
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
            cidade=cidade,
            grau=grau,
            densidade=densidade,
            nivel=nivel,
            nivel_label=cfg["label"],
        )

    for u in grafo:
        for v in grafo[u]:
            if u < v:
                info = arestas_info.get(tuple(sorted((u, v))), {})
                peso = info.get("peso", grafo[u][v])
                net.add_edge(
                    u,
                    v,
                    color=COR_ARESTA,
                    width=1,
                    id=f"{u}_{v}",
                    title="",
                    peso=peso,
                    tipo=info.get("tipo", "N/A"),
                    justificativa=info.get("justificativa", "N/A"),
                )
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
          "damping": 0.95,
          "avoidOverlap": 1
        },
        "stabilization": { "iterations": 300, "fit": true }
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

        ui = """<div style="position:fixed; top:0; left:0; right:0; z-index:999; background:#1e293b; padding:14px 24px; display:flex; align-items:center; gap:14px; flex-wrap:wrap; border-bottom:1px solid #334155; box-shadow:0 2px 8px #0008;">
            <span style="color:#f8fafc; font-weight:700; font-size:18px; margin-right:4px;">Aeroportos</span>
            <a href="subgrafo_hubs.html?v=3" class="reg-btn" style="color:#06b6d4;border-color:#06b6d4;">&#9733; Subgrafo Hubs</a>
            <a href="arvore_percurso.html?v=3" class="reg-btn" style="color:#06b6d4;border-color:#06b6d4;">&#10230; Arvore de Percurso</a>
            <style>.reg-btn,.rota-btn{display:inline-flex;align-items:center;background:#0f172a;color:#94a3b8;border:1px solid #475569;border-radius:6px;padding:7px 14px;font-size:14px;cursor:pointer;font-family:inherit;text-decoration:none;}.reg-btn:hover,.rota-btn:hover{color:#e2e8f0;}.reg-btn.reg-on,.rota-btn.rota-on{color:#f8fafc;border-color:#f8fafc;background:#1e293b;}.reg-dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:7px;}.rota-btn.rota-on{border-color:#facc15;color:#facc15;background:#292524;}</style>
            <span style="color:#f8fafc; font-size:14px; font-weight:800; text-transform:uppercase; letter-spacing:.06em; margin-left:4px;">Regiao:</span>
            <button class="reg-btn reg-on" data-reg="todos" onclick="filtrarRegiao('todos')">Todos</button>
            <button class="reg-btn" data-reg="Norte" onclick="filtrarRegiao('Norte')"><span class="reg-dot" style="background:#60a5fa;"></span>Norte</button>
            <button class="reg-btn" data-reg="Nordeste" onclick="filtrarRegiao('Nordeste')"><span class="reg-dot" style="background:#f97316;"></span>Nordeste</button>
            <button class="reg-btn" data-reg="Sudeste" onclick="filtrarRegiao('Sudeste')"><span class="reg-dot" style="background:#f43f5e;"></span>Sudeste</button>
            <button class="reg-btn" data-reg="Sul" onclick="filtrarRegiao('Sul')"><span class="reg-dot" style="background:#4ade80;"></span>Sul</button>
            <button class="reg-btn" data-reg="Centro-Oeste" onclick="filtrarRegiao('Centro-Oeste')"><span class="reg-dot" style="background:#facc15;"></span>Centro-Oeste</button>
            <span style="color:#f8fafc; font-size:14px; font-weight:800; text-transform:uppercase; letter-spacing:.06em; margin-left:4px;">Rotas:</span>
            <button class="rota-btn" data-rota="rec-poa" onclick="destacarRotaObrigatoria('rec-poa')">REC → POA</button>
            <button class="rota-btn" data-rota="mao-gru" onclick="destacarRotaObrigatoria('mao-gru')">MAO → GRU</button>
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
        <div style="
            position:fixed; top:110px; left:20px; z-index:999;
            background:#1e293b; padding:14px 18px; border-radius:10px;
            color:#e2e8f0; font-size:12px; border:1px solid #334155;
            box-shadow:0 4px 16px #0007; line-height:1; width:260px;
        ">
            <div style="font-weight:700; font-size:13px; color:#f8fafc;
                        margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid #334155;">
                Buscar Caminho
            </div>
            <div style="display:flex; flex-direction:column; gap:8px;">
                <style>
                .ac-wrap{position:relative;}
                .ac-drop{display:none;position:absolute;top:calc(100% + 4px);left:0;right:0;
                    background:#1e293b;border:1px solid #475569;border-radius:6px;
                    z-index:2000;max-height:180px;overflow-y:auto;box-shadow:0 4px 16px #0009;}
                .ac-drop.open{display:block;}
                .ac-item{padding:7px 10px;font-size:13px;color:#cbd5e1;cursor:pointer;display:flex;align-items:center;gap:8px;}
                .ac-item:hover,.ac-item.ac-sel{background:#334155;color:#f1f5f9;}
                .ac-iata{font-weight:700;color:#f1f5f9;min-width:34px;}
                .ac-cidade{color:#64748b;font-size:12px;}
                </style>
                <div>
                    <div style="color:#64748b; font-size:11px; margin-bottom:4px; text-transform:uppercase; letter-spacing:.05em;">Origem</div>
                    <div class="ac-wrap">
                        <input id="origemBusca" placeholder="ex: REC" autocomplete="off" style="
                            width:100%; box-sizing:border-box;
                            padding:7px 10px; border-radius:6px;
                            border:1px solid #475569; background:#0f172a;
                            color:#f1f5f9; font-size:13px; font-family:inherit;
                            outline:none;
                        ">
                        <div id="origemDrop" class="ac-drop"></div>
                    </div>
                </div>
                <div>
                    <div style="color:#64748b; font-size:11px; margin-bottom:4px; text-transform:uppercase; letter-spacing:.05em;">Destino</div>
                    <div class="ac-wrap">
                        <input id="destinoBusca" placeholder="ex: POA" autocomplete="off" style="
                            width:100%; box-sizing:border-box;
                            padding:7px 10px; border-radius:6px;
                            border:1px solid #475569; background:#0f172a;
                            color:#f1f5f9; font-size:13px; font-family:inherit;
                            outline:none;
                        ">
                        <div id="destinoDrop" class="ac-drop"></div>
                    </div>
                </div>
                <div>
                    <div style="color:#64748b; font-size:11px; margin-bottom:4px; text-transform:uppercase; letter-spacing:.05em;">Algoritmo</div>
                    <select id="modoBusca" style="
                        width:100%; box-sizing:border-box;
                        padding:7px 10px; border-radius:6px;
                        border:1px solid #475569; background:#0f172a;
                        color:#f1f5f9; font-size:13px; font-family:inherit;
                        outline:none; cursor:pointer;
                    ">
                        <option value="dijkstra">Dijkstra</option>
                        <option value="bfs">BFS</option>
                        <option value="dfs">DFS</option>
                    </select>
                </div>
                <button onclick="buscarCaminho()" style="
                    width:100%; padding:8px; border-radius:6px;
                    border:none; background:#3b82f6; color:white;
                    cursor:pointer; font-size:13px; font-weight:600;
                    font-family:inherit; margin-top:2px;
                    transition:background .15s;
                " onmouseover="this.style.background='#2563eb'" onmouseout="this.style.background='#3b82f6'">
                    Traçar Rota
                </button>
                <div id="path-result" style="display:none; margin-top:6px; padding:12px 14px; border-radius:8px;
                    background:#0f172a; border:1px solid #334155;">
                    <div id="path-nodes" style="display:flex; flex-wrap:wrap; align-items:center; gap:5px; margin-bottom:12px;"></div>
                    <div style="display:flex; gap:8px;">
                        <div style="flex:1; background:#1e293b; border-radius:6px; padding:10px 8px; text-align:center;">
                            <div style="color:#64748b; font-size:11px; text-transform:uppercase; letter-spacing:.05em;">Custo</div>
                            <div id="path-custo-val" style="color:#facc15; font-size:20px; font-weight:700; margin-top:4px; line-height:1;"></div>
                        </div>
                        <div style="flex:1; background:#1e293b; border-radius:6px; padding:10px 8px; text-align:center;">
                            <div style="color:#64748b; font-size:11px; text-transform:uppercase; letter-spacing:.05em;">Tempo</div>
                            <div id="path-tempo-val" style="color:#e2e8f0; font-size:20px; font-weight:700; margin-top:4px; line-height:1;"></div>
                        </div>
                        <div style="flex:1; background:#1e293b; border-radius:6px; padding:10px 8px; text-align:center;">
                            <div style="color:#64748b; font-size:11px; text-transform:uppercase; letter-spacing:.05em;">Saltos</div>
                            <div id="path-saltos-val" style="color:#f1f5f9; font-size:20px; font-weight:700; margin-top:4px; line-height:1;"></div>
                        </div>
                    </div>
                </div>
                <span id="path-status" style="display:none;"></span>
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

        function hToStr(h){
            if(h === null || h === undefined) return "—";
            const horas = Math.floor(h);
            const mins  = Math.round((h - horas) * 60);
            return horas > 0
                ? (mins > 0 ? horas + "h " + mins + "min" : horas + "h")
                : mins + "min";
        }

        function prepararAdjacencia(){
            const adj = {};
            network.body.data.nodes.get().forEach(n => { adj[n.id] = []; });
            network.body.data.edges.get().forEach(e => {
                const peso = Number(String(e.peso || "1").replace(",", ".")) || 1;
                if(!adj[e.from]) adj[e.from] = [];
                if(!adj[e.to]) adj[e.to] = [];
                adj[e.from].push({ node: e.to, peso, edgeId: e.id });
                adj[e.to].push({ node: e.from, peso, edgeId: e.id });
            });
            return adj;
        }

        function reconstruirCaminho(prev, origem, destino){
            if(origem === destino) return [origem];
            if(!prev[destino]) return [];
            const caminho = [];
            let atual = destino;
            while(atual){
                caminho.unshift(atual);
                if(atual === origem) break;
                atual = prev[atual];
            }
            return caminho[0] === origem ? caminho : [];
        }

        function buscarBfs(origem, destino, adj){
            const fila = [origem];
            const visitados = new Set([origem]);
            const prev = {};
            while(fila.length){
                const atual = fila.shift();
                if(atual === destino) break;
                for(const prox of adj[atual] || []){
                    if(visitados.has(prox.node)) continue;
                    visitados.add(prox.node);
                    prev[prox.node] = atual;
                    fila.push(prox.node);
                }
            }
            return { caminho: reconstruirCaminho(prev, origem, destino), custo: null };
        }

        function buscarDfs(origem, destino, adj){
            const pilha = [origem];
            const visitados = new Set();
            const prev = {};
            while(pilha.length){
                const atual = pilha.pop();
                if(visitados.has(atual)) continue;
                visitados.add(atual);
                if(atual === destino) break;
                for(const prox of [...(adj[atual] || [])].reverse()){
                    if(visitados.has(prox.node)) continue;
                    if(!prev[prox.node]) prev[prox.node] = atual;
                    pilha.push(prox.node);
                }
            }
            return { caminho: reconstruirCaminho(prev, origem, destino), custo: null };
        }

        function buscarDijkstra(origem, destino, adj){
            const dist = {};
            const prev = {};
            const pendentes = new Set(Object.keys(adj));
            Object.keys(adj).forEach(n => { dist[n] = Infinity; });
            dist[origem] = 0;
            while(pendentes.size){
                let atual = null;
                let melhor = Infinity;
                pendentes.forEach(n => {
                    if(dist[n] < melhor){ melhor = dist[n]; atual = n; }
                });
                if(atual === null || atual === destino) break;
                pendentes.delete(atual);
                for(const prox of adj[atual] || []){
                    if(!pendentes.has(prox.node)) continue;
                    const novo = dist[atual] + prox.peso;
                    if(novo < dist[prox.node]){
                        dist[prox.node] = novo;
                        prev[prox.node] = atual;
                    }
                }
            }
            return {
                caminho: reconstruirCaminho(prev, origem, destino),
                custo: Number.isFinite(dist[destino]) ? dist[destino] : null
            };
        }

        const ALGO_COR = { dijkstra: "#facc15", bfs: "#06b6d4", dfs: "#a855f7" };
        const ALGO_LABEL = { dijkstra: "Dijkstra", bfs: "BFS", dfs: "DFS" };

        // calcula níveis BFS a partir da origem (para colorir por camada)
        function bfsNiveis(origem, adj){
            const nivel = { [origem]: 0 };
            const fila = [origem];
            while(fila.length){
                const atual = fila.shift();
                for(const prox of adj[atual] || []){
                    if(nivel[prox.node] === undefined){
                        nivel[prox.node] = nivel[atual] + 1;
                        fila.push(prox.node);
                    }
                }
            }
            return nivel;
        }

        function destacarCaminho(caminho, modo, niveis){
            resetGraph();
            const cor = ALGO_COR[modo] || "#facc15";
            const rotaSet = new Set(caminho);
            const pares = new Set();
            for(let i = 0; i < caminho.length - 1; i++){
                pares.add(caminho[i] + "_" + caminho[i + 1]);
                pares.add(caminho[i + 1] + "_" + caminho[i]);
            }
            network.body.data.nodes.get().forEach(n => {
                const ativo = rotaSet.has(n.id);
                const isFirst = n.id === caminho[0], isLast = n.id === caminho[caminho.length-1];
                let bg;
                if(isFirst)       bg = "#2ecc71";
                else if(isLast)   bg = "#f43f5e";
                else if(ativo)    bg = cor;
                else              bg = COR_NIVEL[n.nivel] || "#94a3b8";
                network.body.data.nodes.update({
                    id: n.id, hidden: false,
                    color: { background: bg },
                    borderWidth: ativo ? 5 : (n.nivel <= 2 ? 4 : 1)
                });
            });

            network.body.data.edges.get().forEach(edge => {
                const ativo = pares.has(edge.from + "_" + edge.to);
                network.body.data.edges.update({
                    id: edge.id, hidden: false,
                    color: { color: ativo ? cor : "#1e3a5f", opacity: ativo ? 1 : 0.55 },
                    width: ativo ? 6 : 1, dashes: false
                });
            });

            try { network.fit({ nodes: caminho, animation: { duration: 500 } }); } catch(_) {}
        }

        function buscarCaminho(){
            const origem = document.getElementById("origemBusca").value.trim().toUpperCase();
            const destino = document.getElementById("destinoBusca").value.trim().toUpperCase();
            const modo = document.getElementById("modoBusca").value;
            if(!origem || !destino) return;
            if(!network.body.data.nodes.get(origem)){
                alert("Aeroporto de origem não encontrado: " + origem);
                return;
            }
            if(!network.body.data.nodes.get(destino)){
                alert("Aeroporto de destino não encontrado: " + destino);
                return;
            }

            const adj = prepararAdjacencia();
            const resultado =
                modo === "bfs" ? buscarBfs(origem, destino, adj) :
                modo === "dfs" ? buscarDfs(origem, destino, adj) :
                buscarDijkstra(origem, destino, adj);

            if(!resultado.caminho.length){
                alert("Nenhum caminho encontrado entre " + origem + " e " + destino);
                return;
            }

            const niveis = modo === "bfs" ? bfsNiveis(origem, adj) : null;
            const custo = resultado.custo;
            destacarCaminho(resultado.caminho, modo, niveis);

            // painel de resultado
            const algoCor = ALGO_COR[modo] || "#facc15";
            const panel = document.getElementById("path-result");
            const nodesEl = document.getElementById("path-nodes");
            nodesEl.innerHTML = resultado.caminho.map((iata, i) => {
                const isFirst = i === 0, isLast = i === resultado.caminho.length - 1;
                const cor = isFirst ? "#2ecc71" : isLast ? "#f43f5e" : algoCor;
                const arrow = i < resultado.caminho.length - 1
                    ? `<span style="color:${algoCor}55; font-size:12px;">→</span>` : "";
                return `<span style="background:#1e293b; border:1px solid ${cor}; color:${cor};
                    border-radius:5px; padding:3px 8px; font-size:12px; font-weight:700;">${iata}</span>${arrow}`;
            }).join("");
            document.getElementById("path-custo-val").style.color = algoCor;
            document.getElementById("path-custo-val").textContent = custo !== null ? custo.toFixed(2) : "—";
            document.getElementById("path-tempo-val").textContent = custo !== null ? hToStr(custo) : (modo !== "dijkstra" ? "n/a (sem peso)" : "");
            document.getElementById("path-saltos-val").textContent = resultado.caminho.length - 1;
            panel.style.display = "block";
        }
        // autocomplete aeroportos
        const AERO_LIST = network.body.data.nodes.get().map(n => ({
            iata: n.id,
            cidade: (n.title || "").replace(/<[^>]+>/g,"").split("\\n")[0] || n.id
        })).sort((a,b) => a.iata.localeCompare(b.iata));

        function setupAC(inputId, dropId){
            const inp = document.getElementById(inputId);
            const drop = document.getElementById(dropId);
            let selIdx = -1;

            function renderDrop(q){
                const items = q
                    ? AERO_LIST.filter(a => a.iata.startsWith(q) || a.cidade.toUpperCase().includes(q))
                    : AERO_LIST;
                if(!items.length){ drop.classList.remove("open"); return; }
                selIdx = -1;
                drop.innerHTML = items.map((a,i) =>
                    `<div class="ac-item" data-iata="${a.iata}" data-idx="${i}">
                        <span class="ac-iata">${a.iata}</span>
                        <span class="ac-cidade">${a.cidade}</span>
                    </div>`
                ).join("");
                drop.querySelectorAll(".ac-item").forEach(el => {
                    el.addEventListener("mousedown", e => {
                        e.preventDefault();
                        inp.value = el.dataset.iata;
                        drop.classList.remove("open");
                    });
                });
                drop.classList.add("open");
            }

            inp.addEventListener("focus", () => renderDrop(inp.value.trim().toUpperCase()));
            inp.addEventListener("input", () => renderDrop(inp.value.trim().toUpperCase()));
            inp.addEventListener("blur",  () => setTimeout(() => drop.classList.remove("open"), 150));
            inp.addEventListener("keydown", e => {
                const items = drop.querySelectorAll(".ac-item");
                if(e.key === "ArrowDown"){ e.preventDefault(); selIdx=Math.min(selIdx+1,items.length-1); }
                else if(e.key === "ArrowUp"){ e.preventDefault(); selIdx=Math.max(selIdx-1,0); }
                else if(e.key === "Enter"){
                    if(selIdx >= 0 && items[selIdx]){ inp.value = items[selIdx].dataset.iata; drop.classList.remove("open"); }
                    else buscarCaminho();
                    return;
                } else if(e.key === "Escape"){ drop.classList.remove("open"); return; }
                items.forEach((el,i) => el.classList.toggle("ac-sel", i===selIdx));
                if(items[selIdx]) items[selIdx].scrollIntoView({block:"nearest"});
            });
        }
        setupAC("origemBusca","origemDrop");
        setupAC("destinoBusca","destinoDrop");
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
                <span style="color:#cbd5e1; font-size:14px; font-weight:600;">${data.cidade || ""}</span>
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
        let hoveredEdge = null;
        let hoveredEdgeBackup = null;

        network.on("hoverEdge", function(params){
            const edge = network.body.data.edges.get(params.edge);
            if(!edge) return;
            hoveredEdge = params.edge;
            hoveredEdgeBackup = {
                color: edge.color,
                width: edge.width,
                dashes: edge.dashes
            };
            network.body.data.edges.update({
                id: edge.id,
                color: { color: "#facc15", opacity: 1 },
                width: Math.max(edge.width || 1, 5),
                dashes: false
            });

            tt.innerHTML = `
              <div style="font-size:17px; font-weight:800; color:#f8fafc; margin-bottom:8px;
                          border-bottom:1px solid #334155; padding-bottom:6px;
                          display:flex; align-items:center; gap:8px;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#facc15" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                ${edge.from} — ${edge.to}
              </div>
              <table style="border-collapse:collapse; width:100%;">
                <tr>
                  <td style="color:#94a3b8; padding:3px 0; padding-right:14px;">Tipo de conexao</td>
                  <td style="color:#e2e8f0; font-weight:600;">${edge.tipo || "N/A"}</td>
                </tr>
                <tr>
                  <td style="color:#94a3b8; padding:3px 0; padding-right:14px;">Custo</td>
                  <td style="color:#facc15; font-weight:700;">${edge.peso || "N/A"}</td>
                </tr>
                <tr>
                  <td style="color:#94a3b8; padding:3px 0; padding-right:14px;">Tempo real</td>
                  <td style="color:#e2e8f0; font-weight:600;">${hToStr(Number(edge.peso))}</td>
                </tr>
                <tr>
                  <td style="color:#94a3b8; padding:3px 0; padding-right:14px;">Descricao</td>
                  <td style="color:#e2e8f0; font-weight:600;">${edge.justificativa || "N/A"}</td>
                </tr>
              </table>
            `;
            tt.style.display = "block";
        });

        network.on("blurEdge", function(){
            if(hoveredEdge && hoveredEdgeBackup){
                network.body.data.edges.update({
                    id: hoveredEdge,
                    color: hoveredEdgeBackup.color,
                    width: hoveredEdgeBackup.width,
                    dashes: hoveredEdgeBackup.dashes
                });
            }
            hoveredEdge = null;
            hoveredEdgeBackup = null;
            tt.style.display = "none";
        });
        let selectedNode = null;
        const COR_NIVEL = { 1: "#f43f5e", 2: "#f97316", 3: "#facc15", 4: "#34d399", 5: "#94a3b8" };

        function filtrarRegiao(regiao){
            const nos = network.body.data.nodes;
            const ars = network.body.data.edges;
            const visiveis = new Set();
            nos.get().forEach(n => {
                const mostra = (regiao === "todos") || (n.regiao === regiao);
                if(mostra) visiveis.add(n.id);
                nos.update({ id: n.id, hidden: !mostra });
            });
            ars.get().forEach(e => {
                const mostra = (regiao === "todos") || (visiveis.has(e.from) && visiveis.has(e.to));
                ars.update({ id: e.id, hidden: !mostra });
            });
            document.querySelectorAll(".reg-btn").forEach(b => b.classList.remove("reg-on"));
            const ativo = document.querySelector('.reg-btn[data-reg="' + regiao + '"]');
            if(ativo) ativo.classList.add("reg-on");
            try { network.fit({ animation: true }); } catch(_) {}
        }

        function resetGraph(){
            document.querySelectorAll(".rota-btn").forEach(b => b.classList.remove("rota-on"));
            const status = document.getElementById("path-status");
            if(status) status.textContent = "";
            network.body.data.edges.get().forEach(edge => {
                network.body.data.edges.update({ id: edge.id, color: { color: "#1e3a5f", opacity: 1 }, width: 1 });
            });
            network.body.data.nodes.get().forEach(n => {
                network.body.data.nodes.update({ id: n.id, color: { background: COR_NIVEL[n.nivel] || "#94a3b8" } });
            });
            selectedNode = null;
        }

        const ROTAS_OBRIGATORIAS = {
            "rec-poa": { nos: ["REC", "POA"], label: "REC → POA" },
            "mao-gru": { nos: ["MAO", "GRU"], label: "MAO → GRU" },
        };

        function destacarRotaObrigatoria(id){
            const rota = ROTAS_OBRIGATORIAS[id];
            if(!rota) return;
            resetGraph();

            const rotaSet = new Set(rota.nos);
            const pares = new Set();
            for(let i = 0; i < rota.nos.length - 1; i++){
                const a = rota.nos[i], b = rota.nos[i + 1];
                pares.add(a + "_" + b);
                pares.add(b + "_" + a);
            }

            network.body.data.nodes.get().forEach(n => {
                const ativo = rotaSet.has(n.id);
                network.body.data.nodes.update({
                    id: n.id,
                    hidden: false,
                    color: { background: ativo ? "#facc15" : (COR_NIVEL[n.nivel] || "#94a3b8") },
                    borderWidth: ativo ? 5 : (n.nivel <= 2 ? 4 : 1)
                });
            });

            network.body.data.edges.get().forEach(edge => {
                const ativo = pares.has(edge.from + "_" + edge.to);
                network.body.data.edges.update({
                    id: edge.id,
                    hidden: false,
                    color: { color: ativo ? "#facc15" : "#1e3a5f", opacity: ativo ? 1 : 0.55 },
                    width: ativo ? 6 : 1,
                    dashes: false
                });
            });

            document.querySelectorAll(".reg-btn").forEach(b => b.classList.remove("reg-on"));
            const todos = document.querySelector('.reg-btn[data-reg="todos"]');
            if(todos) todos.classList.add("reg-on");
            document.querySelectorAll(".rota-btn").forEach(b => b.classList.remove("rota-on"));
            const ativo = document.querySelector('.rota-btn[data-rota="' + id + '"]');
            if(ativo) ativo.classList.add("rota-on");

            try {
                network.fit({ nodes: rota.nos, animation: { duration: 500 } });
            } catch(_) {}
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
    plt = _matplotlib_pyplot()
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
    plt = _matplotlib_pyplot()
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
    plt = _matplotlib_pyplot()
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
    from pyvis.network import Network

    _ensure_out()
    graus = {k: len(v) for k, v in grafo.adj.items()}
    hubs = sorted(graus, key=graus.get, reverse=True)[:8]
    hubs_set = set(hubs)
    max_grau = graus[hubs[0]] if hubs else 1
    net = Network(height="100vh", width="100%", bgcolor="#0f172a", font_color="white")

    for h in hubs:
        g = graus[h]
        regiao = aeroportos.get(h, {}).get("regiao", "N/A")
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

        nav = """<div style="position:fixed; top:0; left:0; right:0; z-index:999; background:#1e293b; padding:14px 24px; display:flex; align-items:center; gap:14px; border-bottom:1px solid #334155; box-shadow:0 2px 8px #0008;">
            <a href="#" onclick="history.back();return false;" style="color:#94a3b8; text-decoration:none; font-size:14px; background:#0f172a; padding:7px 14px; border-radius:6px; border:1px solid #475569;">&#8592; Voltar</a>
            <span style="color:#f8fafc; font-weight:700; font-size:18px;">&#9733; Subgrafo &mdash; Top 8 Hubs</span>
        </div>
        <div id="tt" style="
            display:none; position:fixed; z-index:1000; pointer-events:none;
            background:#1e293b; border:1px solid #475569; border-radius:10px;
            padding:12px 16px; color:#f1f5f9; font-size:13px;
            box-shadow:0 4px 20px #0009; min-width:160px; line-height:1;
        "></div>

        <script>
        function hToStr(h){
            if(h === null || h === undefined || isNaN(h)) return "—";
            const horas = Math.floor(h);
            const mins  = Math.round((h - horas) * 60);
            return horas > 0 ? (mins > 0 ? horas+"h "+mins+"min" : horas+"h") : mins+"min";
        }

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

        network.on("hoverEdge", function(params){
            const tt   = document.getElementById("tt");
            const edge = network.body.data.edges.get(params.edge);
            if(!edge) return;
            const peso = parseFloat(String(edge.title || "").match(/[0-9.]+/)?.[0]) || null;
            tt.innerHTML = `
              <div style="font-size:15px; font-weight:800; color:#f8fafc; margin-bottom:8px;
                          border-bottom:1px solid #334155; padding-bottom:6px;
                          display:flex; align-items:center; gap:8px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#facc15" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                ${edge.from} — ${edge.to}
              </div>
              <table style="border-collapse:collapse; width:100%;">
                <tr>
                  <td style="color:#94a3b8; padding:3px 0; padding-right:12px;">Custo</td>
                  <td style="color:#facc15; font-weight:700;">${peso !== null ? peso.toFixed(2) : "N/A"}</td>
                </tr>
                <tr>
                  <td style="color:#94a3b8; padding:3px 0; padding-right:12px;">Tempo real</td>
                  <td style="color:#e2e8f0; font-weight:600;">${hToStr(peso)}</td>
                </tr>
              </table>
            `;
            tt.style.display = "block";
        });

        network.on("blurEdge", function(){
            document.getElementById("tt").style.display = "none";
        });
        </script>
        """

        html = html.replace("</body>", nav + "</body>")
        f.seek(0)
        f.write(html)
        f.truncate()
