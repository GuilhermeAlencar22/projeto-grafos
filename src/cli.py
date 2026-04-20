import argparse
import json
import time
from collections import Counter
from pathlib import Path

from graphs.graph import Graph, print_degree_sample_stats
from graphs.algorithms import (
    bellman_ford,
    bfs,
    dfs,
    dijkstra,
    validar_pesos_para_dijkstra,
)
from graphs.analysis import componente_alcancavel, componente_tem_ciclo
from graphs.io import load_edge_csv_graph

DEFAULT_IMDB_DATASET = "data/dataset_parte2/imdb_edges.csv"
DEFAULT_BELLMAN_IMDB_DATASET = "data/dataset_parte2/imdb_bellman_ford.csv"
DEFAULT_CHECK_SOURCE = "tt0012313"
DEFAULT_ETAPA3_FONTES = "tt0012313,tt0002605,tt0000147"
DEFAULT_REPORT_PATH = Path(__file__).resolve().parents[1] / "out" / "parte2_report.json"

# Acima disto, o report guarda apenas amostra das distancias (grafo IMDb grande).
BELLMAN_FULL_REPORT_MAX_VERTICES = 3000


def _distancias_bellman_json(dist: dict[str, float]) -> dict[str, float | None]:
    """Serializa distancias Bellman-Ford: inf -> null, chaves ordenadas."""
    out: dict[str, float | None] = {}
    for k in sorted(dist.keys()):
        d = dist[k]
        out[k] = None if d == float("inf") else round(float(d), 9)
    return out


def _serialize_bellman_dist_for_report(dist: dict[str, float]) -> dict:
    """Serializa distancias completas ou resumo quando |V| e grande."""
    if len(dist) <= BELLMAN_FULL_REPORT_MAX_VERTICES:
        return _distancias_bellman_json(dist)
    amostra_chaves = sorted(dist.keys())[:40]
    amostra = _distancias_bellman_json({k: dist[k] for k in amostra_chaves})
    return {
        "omitido_por_tamanho": True,
        "n_vertices": len(dist),
        "limite_relatorio_vertices": BELLMAN_FULL_REPORT_MAX_VERTICES,
        "distancias_amostra": amostra,
    }


def _gravar_report_bellman_ford(report_path: Path, execucoes: list[dict]):
    """Substitui a lista bellman_ford no report, preservando demais chaves."""
    if report_path.exists():
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            report = {}
    else:
        report = {}

    _sanear_estrutura_report(report)
    report["bellman_ford"] = execucoes
    _gravar_report_json(report_path, report)


def _default_fonte_bellman(dataset_path: Path) -> str:
    """Fonte padrao sem --source: datasets de validacao bf_* (s/a) ou tconst IMDb.

    imdb_bellman_ford.csv nunca usa 's'; usa um tconst valido (padrao tt0012313).
    """
    nome = dataset_path.name.lower()
    if nome.startswith("bf_validacao_sem"):
        return "s"
    if nome.startswith("bf_validacao_com"):
        return "a"
    return DEFAULT_CHECK_SOURCE


def _cli_bellman_ford(args: argparse.Namespace, projeto_root: Path):
    """Etapa 5 — Bellman-Ford no grafo dirigido IMDb (diretores em comum + diferenca de rating).

    Dataset principal: data/dataset_parte2/imdb_bellman_ford.csv (gerado por build_bellman_dataset.py).

    Datasets de validacao (Bellman-Ford) em testes/ (opcional: --bellman-demo ou fallback).
    """
    report_path = DEFAULT_REPORT_PATH
    imdb_edges_path = (projeto_root / DEFAULT_IMDB_DATASET).resolve()
    bellman_csv_path = (projeto_root / DEFAULT_BELLMAN_IMDB_DATASET).resolve()
    # Datasets de validacao — grafo artificial controlado (sem fluxo principal IMDb).
    bf_padrao = [
        (
            projeto_root / "data/dataset_parte2/testes/bf_validacao_sem_ciclo.csv",
            "s",
        ),
        (
            projeto_root / "data/dataset_parte2/testes/bf_validacao_com_ciclo.csv",
            "a",
        ),
    ]

    dataset_arg = Path(args.dataset).resolve()

    if getattr(args, "bellman_demo", False):
        if dataset_arg != imdb_edges_path:
            print(
                "[cli] AVISO: --bellman-demo ignora --dataset e usa apenas datasets de "
                "validacao em testes/."
            )
        print(
            "[cli] Etapa 5 — datasets de validacao Bellman-Ford (grafo artificial controlado; "
            "bf_validacao_sem_ciclo + bf_validacao_com_ciclo)."
        )
        runs = bf_padrao
    elif dataset_arg != imdb_edges_path:
        fonte = args.source or _default_fonte_bellman(dataset_arg)
        runs = [(dataset_arg, fonte)]
        if dataset_arg.resolve() == bellman_csv_path.resolve():
            print(
                "[cli] Etapa 5 — dataset principal imdb_bellman_ford.csv "
                "(diretores em comum, pesos por rating); "
                f"fonte={fonte}"
            )
        else:
            print(
                f"[cli] Etapa 5 — Bellman-Ford dataset explicito ({dataset_arg.name}); "
                f"fonte={fonte}"
            )
    elif bellman_csv_path.exists():
        fonte = args.source or DEFAULT_CHECK_SOURCE
        runs = [(bellman_csv_path, fonte)]
        print(
            "[cli] Etapa 5 — dataset principal "
            f"{DEFAULT_BELLMAN_IMDB_DATASET} "
            "(grafo dirigido: diretores em comum + rating); "
            f"fonte={fonte}"
        )
    else:
        print(
            "[cli] AVISO: "
            f"{DEFAULT_BELLMAN_IMDB_DATASET} nao encontrado. "
            "Gere com: python src/parte2/build_bellman_dataset.py "
            "--principals <title.principals.tsv.gz> --ratings <title.ratings.tsv.gz> "
            "[--basics <title.basics.tsv.gz>] [--max-edges N]"
        )
        print(
            "[cli] Etapa 5 — fallback para datasets de validacao "
            "(grafo artificial controlado em testes/)."
        )
        runs = bf_padrao

    registros: list[dict] = []
    t0_total = time.perf_counter()

    for caminho_csv, src in runs:
        if not caminho_csv.exists():
            raise FileNotFoundError(f"Arquivo nao encontrado: {caminho_csv}")

        dados = load_edge_csv_graph(
            str(caminho_csv), weight_column="peso", directed=True
        )
        gbf = Graph()
        for u in dados:
            for v, w in dados[u]:
                gbf.add_directed_edge(u, v, w)

        if src not in gbf.adj:
            raise ValueError(f"No fonte invalido para este grafo: {src}")

        t0 = time.perf_counter()
        ciclo_neg, dist = bellman_ford(gbf, src)
        dt = time.perf_counter() - t0

        try:
            ds_rel = caminho_csv.relative_to(projeto_root)
            ds_str = str(ds_rel).replace("\\", "/")
        except ValueError:
            ds_str = str(caminho_csv)

        linha: dict = {
            "dataset": ds_str,
            "source": src,
            "ciclo_negativo": ciclo_neg,
            "distancias": (
                None
                if ciclo_neg
                else _serialize_bellman_dist_for_report(dist)
            ),
            "tempo_s": round(float(dt), 9),
        }
        registros.append(linha)

    _gravar_report_bellman_ford(report_path, registros)

    print(
        "\n=== BELLMAN-FORD — Etapa 5 "
        "(principal: IMDb; testes/: datasets de validacao se usados) ==="
    )
    for r in registros:
        print(f"  {r['dataset']}  source={r['source']}")
        print(
            f"    ciclo_negativo={r['ciclo_negativo']}  "
            f"tempo_s={r['tempo_s']}"
        )
        if r["ciclo_negativo"]:
            print(
                "    distancias omitidas (ciclo negativo alcancavel a partir da fonte)."
            )
        elif isinstance(r["distancias"], dict) and r["distancias"].get(
            "omitido_por_tamanho"
        ):
            print(
                "    distancias: resumo no report (grafo grande; "
                f"n_vertices={r['distancias'].get('n_vertices')})."
            )
        else:
            print(f"    distancias: {r['distancias']}")
    print(f"  Report: {report_path}")
    print(f"  Tempo total CLI: {time.perf_counter() - t0_total:.6f}s")
    print("=== fim BELLMAN-FORD ===\n")


def _metricas_grafo(g2: Graph):
    """Retorna (|V|, |E| não-dir., grau médio, nó de maior grau, grau máximo)."""
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
    """Retorna (quantidade_componentes, tamanho_maior_componente)."""
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
    """Retorna distribuição organizada de graus (grau -> quantidade de nós)."""
    counter = Counter(len(g2.neighbors(n)) for n in g2.get_nodes())
    return {str(grau): qtd for grau, qtd in sorted(counter.items())}


def _sanear_estrutura_report(report: dict) -> None:
    """Remove formato JSON legado da chave 'bfs_dfs'; preserva listas 'bfs' e 'dfs'."""
    report.pop("bfs_dfs", None)
    report.setdefault("bfs", [])
    report.setdefault("dfs", [])
    report.setdefault("dijkstra", [])
    report.setdefault("bellman_ford", [])
    report.setdefault(
        "benchmark",
        {},
    )


def _tempo_segundos_do_item_busca(item: dict) -> float:
    """Segundos numéricos a partir de tempo_s (preferido) ou tempo (legado)."""
    if item.get("tempo_s") is not None:
        return float(item["tempo_s"])
    if item.get("tempo") is not None:
        return float(item["tempo"])
    return 0.0


def _sincronizar_benchmark(report: dict) -> None:
    """Preenche report['benchmark'] de forma padronizada (Etapa 6).

    Copia/normaliza dados de bfs, dfs, dijkstra, bellman_ford e completa BFS/DFS
    com fontes da etapa3 quando ainda não constam (3 fontes distintas típicas).
    """
    meta = {
        "unidade_tempo": "s",
        "relogio": "perf_counter",
        "versao_esquema": 1,
    }

    # --- BFS: listas CLI + complemento etapa3 (fontes não repetidas) ---
    bfs_bench: list[dict] = []
    seen_bfs: set[str] = set()
    for raw in report.get("bfs", []):
        e = dict(raw)
        ts = _tempo_segundos_do_item_busca(e)
        e["tempo_s"] = round(ts, 9)
        e.setdefault("tempo", e["tempo_s"])
        e.setdefault("origem", "cli")
        bfs_bench.append(e)
        if e.get("source"):
            seen_bfs.add(e["source"])
    for bloco in report.get("etapa3", {}).get("por_fonte", []):
        src = bloco.get("source")
        if not src or src in seen_bfs:
            continue
        b_inner = bloco.get("bfs") or {}
        bfs_bench.append(
            {
                "source": src,
                "tempo_s": round(float(b_inner.get("tempo_s", 0)), 9),
                "visitados": b_inner.get("visitados"),
                "origem": "etapa3",
            }
        )
        seen_bfs.add(src)

    # --- DFS: idem ---
    dfs_bench: list[dict] = []
    seen_dfs: set[str] = set()
    for raw in report.get("dfs", []):
        e = dict(raw)
        ts = _tempo_segundos_do_item_busca(e)
        e["tempo_s"] = round(ts, 9)
        e.setdefault("tempo", e["tempo_s"])
        e.setdefault("origem", "cli")
        dfs_bench.append(e)
        if e.get("source"):
            seen_dfs.add(e["source"])
    for bloco in report.get("etapa3", {}).get("por_fonte", []):
        src = bloco.get("source")
        if not src or src in seen_dfs:
            continue
        d_inner = bloco.get("dfs") or {}
        dfs_bench.append(
            {
                "source": src,
                "tempo_s": round(float(d_inner.get("tempo_s", 0)), 9),
                "visitados": d_inner.get("visitados"),
                "origem": "etapa3",
            }
        )
        seen_dfs.add(src)

    # --- Dijkstra / Bellman-Ford: garantir tempo_s numérico ---
    dj_bench: list[dict] = []
    for raw in report.get("dijkstra", []):
        e = dict(raw)
        if e.get("tempo_s") is None:
            e["tempo_s"] = 0.0
        else:
            e["tempo_s"] = round(float(e["tempo_s"]), 9)
        dj_bench.append(e)

    bf_bench: list[dict] = []
    for raw in report.get("bellman_ford", []):
        e = dict(raw)
        if e.get("tempo_s") is None:
            e["tempo_s"] = 0.0
        else:
            e["tempo_s"] = round(float(e["tempo_s"]), 9)
        bf_bench.append(e)

    report["benchmark"] = {
        "meta": meta,
        "bfs": bfs_bench,
        "dfs": dfs_bench,
        "dijkstra": dj_bench,
        "bellman_ford": bf_bench,
    }


def _gravar_report_json(report_path: Path, report: dict) -> None:
    """Escreve report completo com benchmark sincronizado."""
    _sanear_estrutura_report(report)
    _sincronizar_benchmark(report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _atualizar_report_dataset(report_path: Path, dataset_info: dict):
    """Atualiza somente a chave 'dataset', preservando bfs/dfs e demais chaves."""
    if report_path.exists():
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            report = {}
    else:
        report = {}

    _sanear_estrutura_report(report)
    report["dataset"] = dataset_info
    _gravar_report_json(report_path, report)


def _fontes_etapa3(graph: Graph, raw_fontes: str) -> list[str]:
    """Até 3 fontes distintas válidas no grafo (prioriza lista informada)."""
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
    """Lista de componentes conexas (nao dirigido: vizinhanca simetrica)."""
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
    """Cinco pares variados: componente gigante (incl. distancia), sem caminho entre componentes."""
    comps = _enumerar_componentes(graph)
    comps.sort(key=len, reverse=True)
    if not comps or not comps[0]:
        raise ValueError("Grafo vazio.")
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
        raise ValueError(
            "Nao foi possivel montar 5 pares distintos para Dijkstra neste grafo."
        )
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
                    'Cada par deve ser "origem,destino" separados por ; em --dijkstra-pares'
                )
            s, t = bits[0], bits[1]
            if s not in graph.adj or t not in graph.adj:
                raise ValueError(f"No inexistente no grafo: {s} ou {t}")
            out.append((s, t))
        if len(out) < 5:
            raise ValueError(
                "Informe pelo menos 5 pares em --dijkstra-pares (separados por ;)"
            )
        return out
    return _pares_variados_dijkstra_padrao(graph)


def _gravar_report_dijkstra(report_path: Path, execucoes: list[dict]):
    """Substitui a lista dijkstra no report, preservando dataset, bfs, dfs e etapa3."""
    if report_path.exists():
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            report = {}
    else:
        report = {}

    _sanear_estrutura_report(report)
    report["dijkstra"] = execucoes
    _gravar_report_json(report_path, report)


def _atualizar_report_etapa3(report_path: Path, payload: dict):
    """Grava bloco etapa3 sem alterar dataset nem listas bfs/dfs."""
    if report_path.exists():
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            report = {}
    else:
        report = {}

    _sanear_estrutura_report(report)
    report["etapa3"] = payload
    _gravar_report_json(report_path, report)


def _registrar_execucao_busca(
    report_path: Path,
    algoritmo: str,
    source: str,
    tempo: float,
    *,
    visitados: int | None = None,
    primeiros_nos: list | None = None,
    tempo_total_cli: float | None = None,
):
    """Registra execução de BFS/DFS em listas separadas; não altera o bloco dataset."""
    if report_path.exists():
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            report = {}
    else:
        report = {}

    _sanear_estrutura_report(report)
    chave = algoritmo.lower()
    if chave not in ("bfs", "dfs"):
        raise ValueError(f"Algoritmo invalido para registro no report: {algoritmo}")

    ts = round(float(tempo), 9)
    entrada: dict = {
        "source": str(source),
        "tempo_s": ts,
        "tempo": ts,
    }
    if visitados is not None:
        entrada["visitados"] = visitados
    if primeiros_nos is not None:
        entrada["primeiros_nos"] = primeiros_nos
    if tempo_total_cli is not None:
        entrada["tempo_total_cli_s"] = round(float(tempo_total_cli), 9)
        entrada["tempo_total_cli"] = entrada["tempo_total_cli_s"]

    report[chave].append(entrada)

    _gravar_report_json(report_path, report)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=DEFAULT_IMDB_DATASET)
    parser.add_argument(
        "--alg",
        help=(
            "Algoritmo: CHECK, BFS, DFS, ETAPA3, DIJKSTRA, BELLMAN_FORD. "
            "BELLMAN_FORD (Etapa 5): grafo dirigido gerado com diretores em comum e "
            f"diferenca de rating — dataset principal {DEFAULT_BELLMAN_IMDB_DATASET}; "
            f"--source e tconst IMDb (padrao sem --source: {DEFAULT_CHECK_SOURCE}). "
            "Com --dataset padrao imdb_edges.csv usa esse CSV Bellman se existir; senao "
            "datasets de validacao em testes/. --bellman-demo forca esse modo."
        ),
    )
    parser.add_argument("--source")
    parser.add_argument("--weight-col", default="peso")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Ativa logs do loader e estatísticas de grau do grafo.",
    )
    parser.add_argument(
        "--etapa3-fontes",
        default=DEFAULT_ETAPA3_FONTES,
        help=(
            "Etapa 3: até 3 ids IMDb separados por vírgula "
            f'(padrão: {DEFAULT_ETAPA3_FONTES}).'
        ),
    )
    parser.add_argument(
        "--dijkstra-pares",
        default=None,
        help=(
            'Etapa 4: pelo menos 5 pares "origem,destino" separados por ; '
            "(ex.: tt1,tt2;tt3,tt4;...). Padrão: 5 arestas distintas do grafo."
        ),
    )
    parser.add_argument(
        "--bellman-demo",
        action="store_true",
        help=(
            "Somente com --alg BELLMAN_FORD: forca os datasets de validacao em testes/ "
            "(grafo artificial controlado), sem imdb_bellman_ford.csv."
        ),
    )

    args = parser.parse_args()

    projeto_root = Path(__file__).resolve().parents[1]

    if args.alg == "BELLMAN_FORD":
        _cli_bellman_ford(args, projeto_root)
        return

    if args.dataset:
        t0_total = time.perf_counter()
        dataset_path = Path(args.dataset).resolve()
        if dataset_path.suffix.lower() != ".csv":
            raise ValueError(
                "Use um CSV de arestas do IMDb (ex.: data/dataset_parte2/imdb_edges.csv)."
            )
        weight_col = args.weight_col
        if args.alg == "DIJKSTRA":
            weight_col = "peso"
            if args.weight_col != "peso":
                print(
                    "[cli] DIJKSTRA: usa obrigatoriamente a coluna 'peso' (pesos nao negativos)."
                )

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
            _atualizar_report_dataset(DEFAULT_REPORT_PATH, dataset_info)

            print("\n=== CHECK Parte 2 (resumo) ===")
            print(f"  |V| = {n_v}    |E| = {n_e}")
            print(f"  Grau médio: {grau_medio:.4f}")
            print(f"  Maior grau: {no_max} (grau {grau_max})")
            print(f"  Componentes conexas: {qtd_componentes}")
            print(f"  Maior componente: {maior_componente}")
            print(f"  Fonte BFS/DFS: {fonte}")

            t0_bfs = time.perf_counter()
            ordem_bfs, _ = bfs(g2, fonte)
            dt_bfs = time.perf_counter() - t0_bfs
            print(
                f"  BFS: visitados={len(ordem_bfs)}  "
                f"primeiros 5={ordem_bfs[:5]}  tempo={dt_bfs:.4f}s"
            )

            t0_dfs = time.perf_counter()
            ordem_dfs = dfs(g2, fonte)
            dt_dfs = time.perf_counter() - t0_dfs
            print(
                f"  DFS: visitados={len(ordem_dfs)}  "
                f"primeiros 5={ordem_dfs[:5]}  tempo={dt_dfs:.4f}s"
            )

            print(f"  Tempo total: {time.perf_counter() - t0_total:.4f}s")
            print(f"  Report dataset atualizado em: {DEFAULT_REPORT_PATH}")
            print("=== fim CHECK ===\n")

        elif args.alg == "BFS":
            fonte_exec = args.source or DEFAULT_CHECK_SOURCE
            inicio = time.perf_counter()
            resultado, niveis = bfs(g2, fonte_exec)
            fim = time.perf_counter()
            tempo_bfs = fim - inicio

            print("BFS Parte 2 executado com sucesso")
            primeiros = resultado[:10]
            print("Primeiros 10 nós visitados e nível:")
            for n in primeiros:
                print(f"  {n}  (nível {niveis[n]})")
            print("Total visitados:", len(resultado))
            print("Tempo BFS:", tempo_bfs)
            tempo_cli = time.perf_counter() - t0_total
            print("Tempo total (cli):", tempo_cli)
            _registrar_execucao_busca(
                DEFAULT_REPORT_PATH,
                "bfs",
                fonte_exec,
                tempo_bfs,
                visitados=len(resultado),
                primeiros_nos=resultado[:10],
                tempo_total_cli=tempo_cli,
            )
            print(f"Execução registrada em: {DEFAULT_REPORT_PATH}")

        elif args.alg == "DFS":
            fonte_exec = args.source or DEFAULT_CHECK_SOURCE
            inicio = time.perf_counter()
            resultado = dfs(g2, fonte_exec)
            fim = time.perf_counter()
            tempo_dfs = fim - inicio

            print("DFS Parte 2 executado com sucesso")
            print("Total visitados:", len(resultado))
            print("Tempo DFS:", tempo_dfs)
            tempo_cli = time.perf_counter() - t0_total
            print("Tempo total (cli):", tempo_cli)
            _registrar_execucao_busca(
                DEFAULT_REPORT_PATH,
                "dfs",
                fonte_exec,
                tempo_dfs,
                visitados=len(resultado),
                primeiros_nos=resultado[:10],
                tempo_total_cli=tempo_cli,
            )
            print(f"Execução registrada em: {DEFAULT_REPORT_PATH}")

        elif args.alg == "ETAPA3":
            fontes = _fontes_etapa3(g2, args.etapa3_fontes)
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
                        "source": s,
                        "componente": {
                            "tamanho": tam_comp,
                            "ciclo": ciclo,
                        },
                        "bfs": {
                            "source": s,
                            "visitados": len(ordem_b),
                            "camadas": camadas,
                            "tamanho_componente_alcancada": len(ordem_b),
                            "amostra_ordem": ordem_b[:15],
                            "tempo_s": round(float(dt_b), 9),
                        },
                        "dfs": {
                            "source": s,
                            "visitados": len(ordem_d),
                            "ciclo_na_componente": ciclo,
                            "amostra_ordem": ordem_d[:15],
                            "tempo_s": round(float(dt_d), 9),
                        },
                    }
                )

            tempo_cli = time.perf_counter() - t0_total
            payload_etapa3 = {
                "descricao": "Formalizacao BFS/DFS com 3 fontes distintas (Parte 2)",
                "fontes_utilizadas": fontes,
                "por_fonte": por_fonte,
                "tempo_total_cli_s": round(float(tempo_cli), 9),
            }
            _atualizar_report_etapa3(DEFAULT_REPORT_PATH, payload_etapa3)

            print("\n=== ETAPA 3 — BFS/DFS formal ===")
            for bloco in por_fonte:
                print(f"  Fonte {bloco['source']}:")
                print(
                    f"    componente: |V|={bloco['componente']['tamanho']}  "
                    f"ciclo={bloco['componente']['ciclo']}"
                )
                print(
                    f"    BFS: visitados={bloco['bfs']['visitados']}  "
                    f"camadas={bloco['bfs']['camadas']}  "
                    f"tempo={bloco['bfs']['tempo_s']}s"
                )
                print(
                    f"    DFS: visitados={bloco['dfs']['visitados']}  "
                    f"tempo={bloco['dfs']['tempo_s']}s"
                )
            print(f"  Tempo total CLI: {payload_etapa3['tempo_total_cli_s']}s")
            print(f"  Report atualizado: {DEFAULT_REPORT_PATH}")
            print("=== fim ETAPA 3 ===\n")

        elif args.alg == "DIJKSTRA":
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
                            "source": src,
                            "target": tgt,
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
                        "source": src,
                        "target": tgt,
                        "sem_caminho": False,
                        "custo_total": round(float(custo), 9),
                        "tamanho_caminho": len(caminho),
                        "caminho": caminho[:10],
                        "tempo_s": round(float(dt), 9),
                    }
                    registros.append(linha)

            _gravar_report_dijkstra(DEFAULT_REPORT_PATH, registros)
            print("\n=== DIJKSTRA (Etapa 4) ===")
            for r in registros:
                if r.get("sem_caminho"):
                    print(f"  {r['source']} -> {r['target']}: sem caminho")
                else:
                    print(
                        f"  {r['source']} -> {r['target']}: "
                        f"custo={r['custo_total']} "
                        f"nos={r['tamanho_caminho']} "
                        f"tempo={r['tempo_s']}s"
                    )
            print(f"  Report: {DEFAULT_REPORT_PATH}")
            print("=== fim DIJKSTRA ===\n")

if __name__ == "__main__":
    main()