"""cli parte 2: imdb + report json."""

import argparse
import csv
import time
from collections import Counter
from pathlib import Path

from src.graphs.algorithms import (
    bellman_ford,
    bfs,
    dfs,
    dijkstra,
    validar_pesos_para_dijkstra,
)
from src.graphs.analysis import componente_alcancavel, componente_tem_ciclo
from src.graphs.graph import Graph, print_degree_sample_stats
from src.graphs.io import load_edge_csv_graph
from src.parte2.relatorio import (
    CHAVE_BFS,
    CHAVE_DFS,
    DEFAULT_REPORT_PATH,
    atualizar_report_dataset,
    distancias_bellman_pro_relatorio,
    gravar_bloco_tres_fontes,
    gravar_report_bellman_ford,
    gravar_report_dijkstra,
    registrar_execucao_busca,
)

DEFAULT_IMDB_DATASET = "data/dataset_parte2/Imdb_arestas.csv"
DEFAULT_CHECK_SOURCE = "Jurassic Park"
DEFAULT_TRES_FONTES = "Jurassic Park,Forrest Gump,Pulp Fiction"


def _carregar_bellman_csv(path: Path) -> Graph:
    graph = Graph()
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            origem = (row.get("origem") or "").strip()
            destino = (row.get("destino") or "").strip()
            if not origem or not destino:
                continue
            graph.add_directed_edge(origem, destino, float(row["peso"]))
    return graph


def _cli_bellman_ford(args: argparse.Namespace, projeto_root: Path):
    report_path = DEFAULT_REPORT_PATH
    base = projeto_root / "data" / "dataset_parte2" / "artificiais_bellman_ford"
    casos = [
        (
            base / "bf_validacao_sem_ciclo.csv",
            "Z",
        ),
        (
            base / "bf_validacao_com_ciclo.csv",
            "a",
        ),
    ]
    print("[cli] bellman: casos artificiais via csv.")

    registros: list[dict] = []
    t0_total = time.perf_counter()

    for path_caso, src in casos:
        if not path_caso.exists():
            raise FileNotFoundError(f"csv bellman nao encontrado: {path_caso}")

        gbf = _carregar_bellman_csv(path_caso)

        if src not in gbf.adj:
            raise ValueError(f"fonte invalida no grafo: {src}")

        t0 = time.perf_counter()
        ciclo_neg, dist = bellman_ford(gbf, src)
        dt = time.perf_counter() - t0

        linha: dict = {
            "dataset": str(path_caso.relative_to(projeto_root)),
            "origem": src,
            "ciclo_negativo": ciclo_neg,
            "distancias": (
                None
                if ciclo_neg
                else distancias_bellman_pro_relatorio(dist)
            ),
            "tempo_s": round(float(dt), 9),
        }
        registros.append(linha)

    gravar_report_bellman_ford(report_path, registros)

    print("\n=== bellman ===")
    for r in registros:
        print(f"  {r['dataset']}  origem={r['origem']}")
        print(
            f"    ciclo_negativo={r['ciclo_negativo']}  "
            f"tempo_s={r['tempo_s']}"
        )
        if r["ciclo_negativo"]:
            print("    sem distancias (ciclo negativo a partir da fonte).")
        elif isinstance(r["distancias"], dict) and r["distancias"].get(
            "omitido_por_tamanho"
        ):
            print(
                "    distancias: resumo no report "
                f"(n_vertices={r['distancias'].get('n_vertices')})."
            )
        else:
            print(f"    distancias: {r['distancias']}")
    print(f"  report: {report_path}")
    print(f"  tempo total cli: {time.perf_counter() - t0_total:.6f}s")
    print("=== fim bellman ===\n")


def _metricas_grafo(g2: Graph):
    nodes = g2.get_nodes()
    if not nodes:
        return 0, 0, 0.0, None, 0
    n = len(nodes)
    total_deg = sum(len(g2.neighbors(v)) for v in nodes)
    e = total_deg // 2
    avg = total_deg / n
    max_node = max(nodes, key=lambda v: len(g2.neighbors(v)))
    max_deg = len(g2.neighbors(max_node))
    return n, e, avg, max_node, max_deg


def _metricas_componentes(g2: Graph):
    visited = set()
    componentes = 0
    maior = 0

    for start in g2.get_nodes():
        if start in visited:
            continue

        componentes += 1
        stack = [start]
        tamanho = 0
        visited.add(start)

        while stack:
            node = stack.pop()
            tamanho += 1
            for vizinho, _ in g2.neighbors(node):
                if vizinho not in visited:
                    visited.add(vizinho)
                    stack.append(vizinho)

        maior = max(maior, tamanho)

    return componentes, maior


def _distribuicao_graus(g2: Graph):
    counter = Counter(len(g2.neighbors(n)) for n in g2.get_nodes())
    return {str(grau): qtd for grau, qtd in sorted(counter.items())}


def _tres_fontes_no_grafo(graph: Graph, raw_fontes: str) -> list[str]:
    candidatos = [x.strip() for x in raw_fontes.split(",") if x.strip()]
    escolhidos = []
    for c in candidatos:
        if c in graph.adj and c not in escolhidos:
            escolhidos.append(c)
        if len(escolhidos) >= 3:
            break
    if len(escolhidos) < 3:
        for n in sorted(graph.get_nodes()):
            if n not in escolhidos:
                escolhidos.append(n)
            if len(escolhidos) >= 3:
                break
    return escolhidos[:3]


def _enumerar_componentes(graph: Graph) -> list[list[str]]:
    visitados: set[str] = set()
    comps: list[list[str]] = []
    for start in graph.get_nodes():
        if start in visitados:
            continue
        pilha = [start]
        visitados.add(start)
        comp: list[str] = []
        while pilha:
            u = pilha.pop()
            comp.append(u)
            for v, _ in graph.neighbors(u):
                if v not in visitados:
                    visitados.add(v)
                    pilha.append(v)
        comps.append(comp)
    return comps


def _pares_variados_dijkstra_padrao(graph: Graph) -> list[tuple[str, str]]:
    comps = _enumerar_componentes(graph)
    comps.sort(key=len, reverse=True)
    if not comps or not comps[0]:
        raise ValueError("grafo vazio")
    giant = comps[0]
    hub = giant[0]

    seen = set()

    def par_chave(a: str, b: str) -> tuple[str, str]:
        return tuple(sorted((a, b)))

    def tentar_adicionar(out: list[tuple[str, str]], s: str, t: str) -> bool:
        if s == t:
            return False
        k = par_chave(s, t)
        if k in seen:
            return False
        seen.add(k)
        out.append((s, t))
        return True

    out: list[tuple[str, str]] = []

    outras = [c for c in comps[1:] if c]
    outras.sort(key=len)
    if outras:
        tentar_adicionar(out, hub, outras[0][0])

    for v, _ in graph.neighbors(hub):
        if tentar_adicionar(out, hub, v):
            break

    _, niveis = bfs(graph, hub)
    if niveis:
        dist_max = max(niveis.values())
        mais_longe = max(niveis.keys(), key=lambda x: niveis[x])
        if len(out) < 5:
            tentar_adicionar(out, hub, mais_longe)

        _, n2 = bfs(graph, mais_longe)
        if n2 and len(out) < 5:
            diam_aprox = max(n2.keys(), key=lambda x: n2[x])
            tentar_adicionar(out, mais_longe, diam_aprox)

        if dist_max > 2 and len(out) < 5:
            alvo_nivel = max(1, dist_max // 2)
            mid = next(
                (n for n, nv in niveis.items() if nv == alvo_nivel and n != hub),
                None,
            )
            if mid is not None:
                tentar_adicionar(out, hub, mid)

    if len(out) < 5:
        for u in giant:
            if len(out) >= 5:
                break
            for v, _ in graph.neighbors(u):
                if len(out) >= 5:
                    break
                tentar_adicionar(out, u, v)

    if len(out) < 5:
        nos_g = giant[:]
        for i, a in enumerate(nos_g):
            if len(out) >= 5:
                break
            for b in nos_g[i + 1 :]:
                if tentar_adicionar(out, a, b):
                    if len(out) >= 5:
                        break

    if len(out) < 5:
        raise ValueError("nao da pra montar 5 pares distintos pro dijkstra")
    return out[:5]


def _pares_dijkstra_do_cli(graph: Graph, raw: str | None) -> list[tuple[str, str]]:
    if raw and raw.strip():
        out = []
        for parte in raw.split(";"):
            parte = parte.strip()
            if not parte:
                continue
            bits = [x.strip() for x in parte.split(",")]
            if len(bits) != 2:
                raise ValueError(
                    'cada trecho: "origem,destino" separado por ; (--dijkstra-pares)'
                )
            s, t = bits[0], bits[1]
            if s not in graph.adj or t not in graph.adj:
                raise ValueError(f"vertice fora do grafo: {s} ou {t}")
            out.append((s, t))
        if len(out) < 5:
            raise ValueError("minimo 5 pares em --dijkstra-pares (separados por ;)")
        return out
    return _pares_variados_dijkstra_padrao(graph)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=DEFAULT_IMDB_DATASET)
    parser.add_argument(
        "--alg",
        help=(
            "check, bfs, dfs, tres_fontes, dijkstra, bellman_ford. "
            "bellman: casos artificiais via csv; --dataset ignorado. "
            "--bellman-demo opcional. demais: Imdb_arestas; --source nome do filme "
            f"(default {DEFAULT_CHECK_SOURCE})."
        ),
    )
    parser.add_argument("--source")
    parser.add_argument("--weight-col", default="peso")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="logs do loader + stats de grau.",
    )
    parser.add_argument(
        "--tres-fontes",
        default=DEFAULT_TRES_FONTES,
        dest="tres_fontes",
        help=(f"ate 3 filmes separados por virgula (default {DEFAULT_TRES_FONTES})."),
    )
    parser.add_argument(
        "--dijkstra-pares",
        default=None,
        help=(
            'minimo 5 pares "origem,destino" separados por ; '
            "senao o cli escolhe 5 pares no grafo."
        ),
    )
    parser.add_argument(
        "--bellman-demo",
        action="store_true",
        help="opcional com bellman_ford; --dataset nao afeta o bellman.",
    )
    return parser


def _executar_check(
    g2: Graph, args: argparse.Namespace, t0_total: float, dataset_path: Path
) -> None:
    # check: metricas + amostra bfs/dfs no terminal (nao grava bfs/dfs no json)
    fonte = args.source or DEFAULT_CHECK_SOURCE
    n_v, n_e, grau_medio, no_max, grau_max = _metricas_grafo(g2)
    graus = [len(g2.neighbors(n)) for n in g2.get_nodes()]
    grau_min = min(graus) if graus else 0
    grau_maximo = max(graus) if graus else 0
    qtd_componentes, maior_componente = _metricas_componentes(g2)
    distribuicao = _distribuicao_graus(g2)

    dataset_info = {
        "nome": dataset_path.name,
        "|V|": n_v,
        "|E|": n_e,
        "num_vertices": n_v,
        "num_arestas": n_e,
        "tipo": "nao-direcionado",
        "ponderado": True,
        "grau": {
            "min": grau_min,
            "max": grau_maximo,
            "medio": round(grau_medio, 6),
        },
        "componentes_conexas": qtd_componentes,
        "maior_componente_conexa": maior_componente,
        "distribuicao_graus": distribuicao,
    }
    atualizar_report_dataset(DEFAULT_REPORT_PATH, dataset_info)

    print("\n=== check ===")
    print(f"  |V| = {n_v}    |E| = {n_e}")
    print(f"  grau medio: {grau_medio:.4f}")
    print(f"  maior grau: {no_max} (grau {grau_max})")
    print(f"  componentes conexas: {qtd_componentes}")
    print(f"  maior componente: {maior_componente}")
    print(f"  fonte bfs/dfs: {fonte}")

    t0_bfs = time.perf_counter()
    ordem_bfs, _ = bfs(g2, fonte)
    dt_bfs = time.perf_counter() - t0_bfs
    print(
        f"  bfs: visitados={len(ordem_bfs)}  "
        f"primeiros 5={ordem_bfs[:5]}  tempo={dt_bfs:.4f}s"
    )

    t0_dfs = time.perf_counter()
    ordem_dfs = dfs(g2, fonte)
    dt_dfs = time.perf_counter() - t0_dfs
    print(
        f"  dfs: visitados={len(ordem_dfs)}  "
        f"primeiros 5={ordem_dfs[:5]}  tempo={dt_dfs:.4f}s"
    )

    print(f"  tempo total: {time.perf_counter() - t0_total:.4f}s")
    print(f"  report: {DEFAULT_REPORT_PATH}")
    print("=== fim check ===\n")


def _executar_bfs(g2: Graph, args: argparse.Namespace, t0_total: float) -> None:
    # bfs: uma fonte + registro no report
    fonte_exec = args.source or DEFAULT_CHECK_SOURCE
    inicio = time.perf_counter()
    resultado, niveis = bfs(g2, fonte_exec)
    fim = time.perf_counter()
    tempo_bfs = fim - inicio

    print("bfs ok")
    primeiros = resultado[:10]
    print("primeiros 10 nos (nivel):")
    for n in primeiros:
        print(f"  {n}  (nivel {niveis[n]})")
    print("total visitados:", len(resultado))
    print("tempo bfs:", tempo_bfs)
    tempo_cli = time.perf_counter() - t0_total
    print("tempo total (cli):", tempo_cli)
    registrar_execucao_busca(
        DEFAULT_REPORT_PATH,
        CHAVE_BFS,
        fonte_exec,
        tempo_bfs,
        visitados=len(resultado),
        primeiros_nos=resultado[:10],
        tempo_total_cli=tempo_cli,
    )
    print(f"gravado em: {DEFAULT_REPORT_PATH}")


def _executar_dfs(g2: Graph, args: argparse.Namespace, t0_total: float) -> None:
    # dfs: uma fonte + registro no report
    fonte_exec = args.source or DEFAULT_CHECK_SOURCE
    inicio = time.perf_counter()
    resultado = dfs(g2, fonte_exec)
    fim = time.perf_counter()
    tempo_dfs = fim - inicio

    print("dfs ok")
    print("total visitados:", len(resultado))
    print("tempo dfs:", tempo_dfs)
    tempo_cli = time.perf_counter() - t0_total
    print("tempo total (cli):", tempo_cli)
    registrar_execucao_busca(
        DEFAULT_REPORT_PATH,
        CHAVE_DFS,
        fonte_exec,
        tempo_dfs,
        visitados=len(resultado),
        primeiros_nos=resultado[:10],
        tempo_total_cli=tempo_cli,
    )
    print(f"gravado em: {DEFAULT_REPORT_PATH}")


def _executar_tres_fontes(g2: Graph, args: argparse.Namespace, t0_total: float) -> None:
    # tres_fontes: bfs/dfs ate tres fontes + bloco no json
    fontes = _tres_fontes_no_grafo(g2, args.tres_fontes)
    por_fonte = []
    for s in fontes:
        comp = componente_alcancavel(g2, s)
        tam_comp = len(comp)
        ciclo = componente_tem_ciclo(g2, comp) if tam_comp else False

        t0_b = time.perf_counter()
        ordem_b, niveis = bfs(g2, s)
        dt_b = time.perf_counter() - t0_b
        camadas = max(niveis.values()) if niveis else 0

        t0_d = time.perf_counter()
        ordem_d = dfs(g2, s)
        dt_d = time.perf_counter() - t0_d

        por_fonte.append(
            {
                "origem": s,
                "componente": {
                    "tamanho": tam_comp,
                    "ciclo": ciclo,
                },
                "bfs": {
                    "origem": s,
                    "visitados": len(ordem_b),
                    "camadas": camadas,
                    "tamanho_componente_alcancada": len(ordem_b),
                    "amostra_ordem": ordem_b[:15],
                    "tempo_s": round(float(dt_b), 9),
                },
                "dfs": {
                    "origem": s,
                    "visitados": len(ordem_d),
                    "ciclo": ciclo,
                    "amostra_ordem": ordem_d[:15],
                    "tempo_s": round(float(dt_d), 9),
                },
            }
        )

    tempo_cli = time.perf_counter() - t0_total
    payload_tres_fontes = {
        "descricao": "bfs/dfs ate tres fontes",
        "fontes_utilizadas": fontes,
        "por_fonte": por_fonte,
        "tempo_total_cli_s": round(float(tempo_cli), 9),
    }
    gravar_bloco_tres_fontes(DEFAULT_REPORT_PATH, payload_tres_fontes)

    print("\n=== tres fontes ===")
    for bloco in por_fonte:
        print(f"  fonte {bloco['origem']}:")
        print(
            f"    componente: |V|={bloco['componente']['tamanho']}  "
            f"ciclo={bloco['componente']['ciclo']}"
        )
        print(
            f"    bfs: visitados={bloco['bfs']['visitados']}  "
            f"camadas={bloco['bfs']['camadas']}  "
            f"tempo={bloco['bfs']['tempo_s']}s"
        )
        print(
            f"    dfs: visitados={bloco['dfs']['visitados']}  "
            f"tempo={bloco['dfs']['tempo_s']}s"
        )
    print(f"  tempo total cli: {payload_tres_fontes['tempo_total_cli_s']}s")
    print(f"  report: {DEFAULT_REPORT_PATH}")
    print("=== fim ===\n")


def _executar_dijkstra(g2: Graph, args: argparse.Namespace) -> None:
    # dijkstra: varios pares + report
    validar_pesos_para_dijkstra(g2)
    pares = _pares_dijkstra_do_cli(g2, args.dijkstra_pares)
    registros = []
    for src, tgt in pares:
        t0p = time.perf_counter()
        resultado = dijkstra(g2, src, tgt)
        dt = time.perf_counter() - t0p
        if resultado is None:
            registros.append(
                {
                    "origem": src,
                    "destino": tgt,
                    "sem_caminho": True,
                    "custo_total": None,
                    "tamanho_caminho": 0,
                    "caminho": [],
                    "tempo_s": round(float(dt), 9),
                }
            )
        else:
            custo, caminho = resultado
            linha = {
                "origem": src,
                "destino": tgt,
                "sem_caminho": False,
                "custo_total": round(float(custo), 9),
                "tamanho_caminho": len(caminho),
                "caminho": caminho[:10],
                "tempo_s": round(float(dt), 9),
            }
            registros.append(linha)

    gravar_report_dijkstra(DEFAULT_REPORT_PATH, registros)
    print("\n=== dijkstra ===")
    for r in registros:
        if r.get("sem_caminho"):
            print(f"  {r['origem']} -> {r['destino']}: sem caminho")
        else:
            print(
                f"  {r['origem']} -> {r['destino']}: "
                f"custo={r['custo_total']} "
                f"nos={r['tamanho_caminho']} "
                f"tempo={r['tempo_s']}s"
            )
    print(f"  report: {DEFAULT_REPORT_PATH}")
    print("=== fim dijkstra ===\n")


def executar_cli(args: argparse.Namespace, projeto_root: Path | None = None) -> None:
    """mesmo fluxo que main depois do parse."""
    if projeto_root is None:
        projeto_root = Path(__file__).resolve().parents[1]

    # bellman: fluxo separado em _cli_bellman_ford
    if args.alg == "BELLMAN_FORD":
        _cli_bellman_ford(args, projeto_root)
        return

    if not args.dataset:
        return

    # grafo nao-dirigido a partir do csv (check, bfs, dfs, ...)
    t0_total = time.perf_counter()
    dataset_path = Path(args.dataset).resolve()
    if dataset_path.suffix.lower() != ".csv":
        raise ValueError("precisa ser csv de arestas (ex. Imdb_arestas.csv).")
    weight_col = args.weight_col
    if args.alg == "DIJKSTRA":
        weight_col = "peso"
        if args.weight_col != "peso":
            print("[cli] dijkstra: forca coluna peso (>=0).")

    print(f"[cli] dataset: {dataset_path}")
    print(f"[cli] coluna de peso: {weight_col}")
    if args.alg:
        print(f"[cli] algoritmo: {args.alg}")

    dados = load_edge_csv_graph(
        str(dataset_path), weight_column=weight_col, debug=args.debug
    )

    g2 = Graph()
    seen_edges = set()
    for origem in dados:
        for destino, peso in dados[origem]:
            edge_key = tuple(sorted((origem, destino)))
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)
            g2.add_edge(origem, destino, peso)

    if args.debug:
        print_degree_sample_stats(g2, sample_size=10)

    if args.alg == "CHECK":
        _executar_check(g2, args, t0_total, dataset_path)
    elif args.alg == "BFS":
        _executar_bfs(g2, args, t0_total)
    elif args.alg == "DFS":
        _executar_dfs(g2, args, t0_total)
    elif args.alg == "TRES_FONTES":
        _executar_tres_fontes(g2, args, t0_total)
    elif args.alg == "DIJKSTRA":
        _executar_dijkstra(g2, args)
    else:
        raise ValueError(f"algoritmo invalido: {args.alg}")


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    executar_cli(args)


if __name__ == "__main__":
    main()
