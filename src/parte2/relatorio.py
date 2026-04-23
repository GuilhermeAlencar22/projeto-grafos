"""le json da parte 2, merge e grava out/parte2_report.json."""

from __future__ import annotations

import json
from pathlib import Path

# chaves fixas do json do relatorio (menos string solta repetida).
CHAVE_BFS = "bfs"
CHAVE_DFS = "dfs"
CHAVE_DIJKSTRA = "dijkstra"
CHAVE_BELLMAN_FORD = "bellman_ford"
CHAVE_BENCHMARK = "benchmark"
CHAVE_TRES_FONTES = "tres_fontes"
CHAVE_DATASET = "dataset"

# caminho padrao: out/parte2_report.json na raiz (parents[2] a partir de src/parte2/).
DEFAULT_REPORT_PATH = Path(__file__).resolve().parents[2] / "out" / "parte2_report.json"

# acima disso, bellman no json vira so amostra (imdb grande).
BELLMAN_FULL_REPORT_MAX_VERTICES = 3000


def _carregar_report(report_path: Path) -> dict:
    """le do disco ou {} se nao existir / json invalido."""
    if not report_path.exists():
        return {}
    try:
        return json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def distancias_bellman_json(dist: dict[str, float]) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    for k in sorted(dist.keys()):
        d = dist[k]
        out[k] = None if d == float("inf") else round(float(d), 9)
    return out


def distancias_bellman_pro_relatorio(dist: dict[str, float]) -> dict:
    if len(dist) <= BELLMAN_FULL_REPORT_MAX_VERTICES:
        return distancias_bellman_json(dist)
    amostra_chaves = sorted(dist.keys())[:40]
    amostra = distancias_bellman_json({k: dist[k] for k in amostra_chaves})
    return {
        "omitido_por_tamanho": True,
        "n_vertices": len(dist),
        "limite_relatorio_vertices": BELLMAN_FULL_REPORT_MAX_VERTICES,
        "distancias_amostra": amostra,
    }


def limpar_estrutura_relatorio(report: dict) -> None:
    report.pop("bfs_dfs", None)
    report.setdefault(CHAVE_BFS, [])
    report.setdefault(CHAVE_DFS, [])
    report.setdefault(CHAVE_DIJKSTRA, [])
    report.setdefault(CHAVE_BELLMAN_FORD, [])
    report.setdefault(CHAVE_BENCHMARK, {})


def tempo_segundos_do_item_busca(item: dict) -> float:
    if item.get("tempo_s") is not None:
        return float(item["tempo_s"])
    if item.get("tempo") is not None:
        return float(item["tempo"])
    return 0.0


def deduplicar_bfs_dfs_por_fonte(itens: list[dict]) -> list[dict]:
    """uma linha por source; fica quem tem mais campo."""

    melhor: dict[str, dict] = {}
    ordem: list[str] = []
    for item in itens:
        src = item.get("source")
        if not src:
            continue
        copia = dict(item)
        if src not in melhor:
            ordem.append(src)
            melhor[src] = copia
        elif len(copia) >= len(melhor[src]):
            melhor[src] = copia
    return [melhor[s] for s in ordem if s in melhor]


def normalizar_campos_tempo_busca(itens: list[dict]) -> None:
    for it in itens:
        ts = tempo_segundos_do_item_busca(it)
        it["tempo_s"] = round(ts, 9)
        it.setdefault("tempo", it["tempo_s"])


def _montar_benchmark_busca_por_fonte(
    report: dict, lista_key: str, inner_key: str
) -> list[dict]:
    """lista pra benchmark bfs/dfs: top-level + bloco tres_fontes."""
    bloco_fontes = report.get(CHAVE_TRES_FONTES) or {}
    bench: list[dict] = []
    seen: set[str] = set()
    for raw in report.get(lista_key, []):
        e = dict(raw)
        ts = tempo_segundos_do_item_busca(e)
        e["tempo_s"] = round(ts, 9)
        e.setdefault("tempo", e["tempo_s"])
        e.setdefault("origem", "cli")
        bench.append(e)
        if e.get("source"):
            seen.add(e["source"])
    for bloco in bloco_fontes.get("por_fonte", []):
        src = bloco.get("source")
        if not src or src in seen:
            continue
        inner = bloco.get(inner_key) or {}
        bench.append(
            {
                "source": src,
                "tempo_s": round(float(inner.get("tempo_s", 0)), 9),
                "visitados": inner.get("visitados"),
                "origem": "tres_fontes",
            }
        )
        seen.add(src)
    return bench


def sincronizar_benchmark(report: dict) -> None:
    meta = {
        "unidade_tempo": "s",
        "relogio": "perf_counter",
        "versao_esquema": 1,
    }

    bfs_bench = _montar_benchmark_busca_por_fonte(report, CHAVE_BFS, CHAVE_BFS)
    dfs_bench = _montar_benchmark_busca_por_fonte(report, CHAVE_DFS, CHAVE_DFS)

    dj_bench: list[dict] = []
    for raw in report.get(CHAVE_DIJKSTRA, []):
        e = dict(raw)
        if e.get("tempo_s") is None:
            e["tempo_s"] = 0.0
        else:
            e["tempo_s"] = round(float(e["tempo_s"]), 9)
        dj_bench.append(e)

    bf_bench: list[dict] = []
    for raw in report.get(CHAVE_BELLMAN_FORD, []):
        e = dict(raw)
        if e.get("tempo_s") is None:
            e["tempo_s"] = 0.0
        else:
            e["tempo_s"] = round(float(e["tempo_s"]), 9)
        bf_bench.append(e)

    report[CHAVE_BENCHMARK] = {
        "meta": meta,
        CHAVE_BFS: bfs_bench,
        CHAVE_DFS: dfs_bench,
        CHAVE_DIJKSTRA: dj_bench,
        CHAVE_BELLMAN_FORD: bf_bench,
    }


def espelhar_tempo_execucao(report: dict) -> None:
    """espelha tempo_s ou tempo em tempo_execucao no dict."""

    def walk(obj):
        if isinstance(obj, dict):
            if obj.get("tempo_execucao") is None:
                if obj.get("tempo_s") is not None:
                    obj["tempo_execucao"] = obj["tempo_s"]
                elif obj.get("tempo") is not None:
                    obj["tempo_execucao"] = obj["tempo"]
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(report)


def gravar_report_json(report_path: Path, report: dict) -> None:
    limpar_estrutura_relatorio(report)
    report[CHAVE_BFS] = deduplicar_bfs_dfs_por_fonte(report.get(CHAVE_BFS, []))
    report[CHAVE_DFS] = deduplicar_bfs_dfs_por_fonte(report.get(CHAVE_DFS, []))
    normalizar_campos_tempo_busca(report[CHAVE_BFS])
    normalizar_campos_tempo_busca(report[CHAVE_DFS])
    sincronizar_benchmark(report)
    espelhar_tempo_execucao(report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _salvar_report(report_path: Path, report: dict) -> None:
    """dedup + benchmark + grava (alias de gravar_report_json)."""
    gravar_report_json(report_path, report)


def gravar_report_bellman_ford(report_path: Path, execucoes: list[dict]) -> None:
    report = _carregar_report(report_path)
    limpar_estrutura_relatorio(report)
    # merge por path de dataset; nao apaga outras entradas
    existente = report.get(CHAVE_BELLMAN_FORD) or []
    chaves_novas = {e.get("dataset") for e in execucoes if e.get("dataset")}
    mantidos = [e for e in existente if e.get("dataset") not in chaves_novas]
    report[CHAVE_BELLMAN_FORD] = mantidos + list(execucoes)
    _salvar_report(report_path, report)


def atualizar_report_dataset(report_path: Path, dataset_info: dict) -> None:
    report = _carregar_report(report_path)
    limpar_estrutura_relatorio(report)
    report[CHAVE_DATASET] = dataset_info
    _salvar_report(report_path, report)


def gravar_report_dijkstra(report_path: Path, execucoes: list[dict]) -> None:
    report = _carregar_report(report_path)
    limpar_estrutura_relatorio(report)
    report[CHAVE_DIJKSTRA] = execucoes
    _salvar_report(report_path, report)


def gravar_bloco_tres_fontes(report_path: Path, payload: dict) -> None:
    report = _carregar_report(report_path)
    limpar_estrutura_relatorio(report)
    report[CHAVE_TRES_FONTES] = payload
    _salvar_report(report_path, report)


def registrar_execucao_busca(
    report_path: Path,
    algoritmo: str,
    source: str,
    tempo: float,
    *,
    visitados: int | None = None,
    primeiros_nos: list | None = None,
    tempo_total_cli: float | None = None,
) -> None:
    report = _carregar_report(report_path)
    limpar_estrutura_relatorio(report)
    chave = algoritmo.lower()
    if chave not in (CHAVE_BFS, CHAVE_DFS):
        raise ValueError(f"so bfs/dfs no report, veio: {algoritmo}")

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

    _salvar_report(report_path, report)
