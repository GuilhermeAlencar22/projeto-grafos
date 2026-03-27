from graphs.graph import Graph
from graphs.algorithms import bfs, dfs

def main():
    g = Graph()

    # exemplo simples
    g.add_edge("REC", "SSA", 1)
    g.add_edge("REC", "GRU", 2)

    print("BFS:", bfs(g, "REC"))
    print("DFS:", dfs(g, "REC"))

if __name__ == "__main__":
    main()