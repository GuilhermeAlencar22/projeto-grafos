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
            title=f"{node} | Grau: {grau}"
        )

    for idx, caminho in enumerate(caminhos):
        cor = cores_rotas[idx % len(cores_rotas)]

        for i in range(len(caminho) - 1):
            u, v = caminho[i], caminho[i + 1]

            net.add_edge(
                u, v,
                color=cor,
                width=6,
                smooth={"type": "dynamic"}
            )

    net.set_options("""
    {
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -30000,
          "springLength": 200
        }
      }
    }
    """)

    net.write_html(output_path)

def gerar_grafo_interativo(grafo, aeroportos, ego_metrics):
    _ensure_out()

    net = Network(height="800px", width="100%", bgcolor="#020617", font_color="white")

    for node in grafo:
        grau = len(grafo[node])
        regiao = aeroportos[node]["regiao"]

        ego = next((e for e in ego_metrics if e["aeroporto"] == node), None)
        densidade = round(ego["densidade_ego"], 3) if ego else 0

        net.add_node(
            node,
            label=node,
            size=10 + grau * 1.5,
            title=f"""
            <b>{node}</b><br>
            Região: {regiao}<br>
            Grau: {grau}<br>
            Densidade: {densidade}
            """
        )

    for u in grafo:
        for v in grafo[u]:
            if u < v:
                net.add_edge(u, v, color="#1e293b", width=1)

    net.set_options("""
    {
      "interaction": {
        "hover": true,
        "navigationButtons": true
      },
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -40000,
          "springLength": 220
        }
      }
    }
    """)

    net.write_html("out/grafo_interativo.html")

    with open("out/grafo_interativo.html", "r+", encoding="utf-8") as f:
        html = f.read()

        ui = """
        <div style="position:fixed;top:20px;right:20px;background:#020617;padding:15px;border-radius:10px;color:white;">
            <input id="search" placeholder="Buscar aeroporto" style="padding:5px;">
            <button onclick="buscar()">Buscar</button>
        </div>

        <script>
        function buscar(){
            let val = document.getElementById("search").value.toUpperCase();
            network.focus(val, {scale:1.5});
        }
        </script>
        """

        html = html.replace("</body>", ui + "</body")

        f.seek(0)
        f.write(html)
        f.truncate()

def plot_histograma_graus(grafo):
    _ensure_out()

    graus = [len(v) for v in grafo.values()]

    plt.figure()
    plt.hist(graus)
    plt.title("Distribuição de Graus")
    plt.xlabel("Grau")
    plt.ylabel("Frequência")
    plt.savefig("out/histograma.png")
    plt.close()


def plot_ranking(grafo):
    _ensure_out()

    graus = {k: len(v) for k, v in grafo.items()}
    top = sorted(graus.items(), key=lambda x: x[1], reverse=True)[:10]

    labels = [k for k, _ in top]
    vals = [v for _, v in top]

    plt.figure()
    plt.bar(labels, vals)
    plt.title("Top 10 Aeroportos Mais Conectados")
    plt.xlabel("Aeroporto")
    plt.ylabel("Grau")
    plt.savefig("out/ranking.png")
    plt.close()


def plot_regioes(grafo, aeroportos):
    _ensure_out()

    soma = defaultdict(int)
    cont = defaultdict(int)

    for n in grafo:
        r = aeroportos[n]["regiao"]
        soma[r] += len(grafo[n])
        cont[r] += 1

    medias = {r: soma[r] / cont[r] for r in soma}

    plt.figure()
    plt.bar(medias.keys(), medias.values())
    plt.title("Grau Médio por Região")
    plt.xlabel("Região")
    plt.ylabel("Grau Médio")
    plt.savefig("out/regioes.png")
    plt.close()


def plot_subgrafo_hubs(grafo, aeroportos):
    _ensure_out()

    graus = {k: len(v) for k, v in grafo.items()}
    hubs = sorted(graus, key=graus.get, reverse=True)[:8]

    net = Network(height="700px", width="100%", bgcolor="#020617", font_color="white")

    for h in hubs:
        net.add_node(h, size=20 + graus[h])

    for u in hubs:
        for v in grafo[u]:
            if v in hubs and u < v:
                net.add_edge(u, v)

    net.write_html("out/subgrafo_hubs.html")