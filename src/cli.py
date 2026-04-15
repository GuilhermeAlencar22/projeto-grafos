import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from graphs.io import carregar_aeroportos, carregar_grafo
from graphs.algorithms import bfs, dfs, dijkstra

def cmd_bfs(grafo, args):
    ordem = bfs(grafo, args.origem)
    if not ordem:
        print(f"Aeroporto '{args.origem}' não encontrado no grafo.")
        return
    print(f"BFS a partir de {args.origem}:")
    print(" -> ".join(ordem))


def cmd_dfs(grafo, args):
    ordem = dfs(grafo, args.origem)
    if not ordem:
        print(f"Aeroporto '{args.origem}' não encontrado no grafo.")
        return
    print(f"DFS a partir de {args.origem}:")
    print(" -> ".join(ordem))


def cmd_dijkstra(grafo, args):
    custo, caminho = dijkstra(grafo, args.origem, args.destino)
    if not caminho:
        print(f"Sem caminho entre {args.origem} e {args.destino}.")
        return
    print(f"Dijkstra de {args.origem} até {args.destino}:")
    print(f"  Caminho: {' -> '.join(caminho)}")
    print(f"  Custo total: {round(custo, 2)}")


def cmd_aeroportos(aeroportos, args):
    regiao = args.regiao.upper() if args.regiao else None
    for codigo, info in sorted(aeroportos.items()):
        if regiao and info["regiao"].upper() != regiao:
            continue
        print(f"  {codigo} — {info['cidade']} ({info['regiao']})")


def main():
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="Rede de Aeroportos do Brasil — interface de linha de comando"
    )

    subparsers = parser.add_subparsers(dest="comando", required=True)
    p_bfs = subparsers.add_parser("bfs", help="Busca em largura a partir de um aeroporto")
    p_bfs.add_argument("origem", help="Código IATA do aeroporto de origem (ex: SSA)")
    p_dfs = subparsers.add_parser("dfs", help="Busca em profundidade a partir de um aeroporto")
    p_dfs.add_argument("origem", help="Código IATA do aeroporto de origem (ex: SSA)")
    p_dijk = subparsers.add_parser("dijkstra", help="Menor caminho entre dois aeroportos")
    p_dijk.add_argument("origem", help="Código IATA de origem (ex: REC)")
    p_dijk.add_argument("destino", help="Código IATA de destino (ex: GRU)")
    p_aero = subparsers.add_parser("aeroportos", help="Lista aeroportos disponíveis")
    p_aero.add_argument("--regiao", help="Filtrar por região (ex: Nordeste)", default=None)

    args = parser.parse_args()
    base = os.path.join(os.path.dirname(__file__), "..", "data")
    aeroportos = carregar_aeroportos(os.path.join(base, "aeroportos_data.csv"))
    grafo = carregar_grafo(os.path.join(base, "adjacencias_aeroportos.csv"))

    if args.comando == "bfs":
        cmd_bfs(grafo, args)
    elif args.comando == "dfs":
        cmd_dfs(grafo, args)
    elif args.comando == "dijkstra":
        cmd_dijkstra(grafo, args)
    elif args.comando == "aeroportos":
        cmd_aeroportos(aeroportos, args)

if __name__ == "__main__":
    main()