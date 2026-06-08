# Projeto Final — Teoria dos Grafos

Projeto dividido em duas partes: **Parte 1** modela a rede de aeroportos brasileiros; **Parte 2** aplica algoritmos de grafos sobre um dataset de filmes do IMDb.

Todos os algoritmos (BFS, DFS, Dijkstra, Bellman-Ford) foram implementados do zero em Python puro, sem bibliotecas de grafos prontas.

---

## Equipe

| Nome | E-mail |
|---|---|
| Guilherme Alencar Augusto Correa | gaac@cesar.school |
| Rodrigo Lucena Cavalcanti | rlc2@cesar.school |
| Rodrigo Torres Galindo Filho | rtgf@cesar.school |
| Erick Acioli Belo | eab2@cesar.school |
| João Marcelo Tavares Pereira Montenegro | jmtpm@cesar.school |

---

## Pré-requisitos

- Python 3.10 ou superior
- Pip atualizado

---

## Instalação

```bash
# 1. Clone o repositório
git clone <url-do-repositorio>
cd projeto-grafos

# 2. (Opcional, recomendado) Crie um ambiente virtual
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Instale as dependências
python -m pip install -r requirements.txt
```

---

## Como executar

> Todos os comandos devem ser rodados a partir da **raiz do projeto** (`projeto-grafos/`).

### Pipeline completo (Parte 1 + Parte 2)

```bash
python -m src.solve
```

Gera todas as saídas em `out/`, os JSONs da interface e os gráficos.

### Apenas Parte 1

```bash
python -m src.solve parte1
```

### Apenas Parte 2

```bash
python -m src.solve parte2
```

### Gerar visualizações da Parte 2 (PNGs)

```bash
python -m src.parte1.viz parte2
```

### Gerar dados da interface web da Parte 2

```bash
python -m src.parte2.build_interface_data
python -m src.parte2.build_interface_grafo
```

### Subir o servidor local e abrir a interface

```bash
python -m http.server 8000 --bind 127.0.0.1
```

Abrir no navegador:

```
http://127.0.0.1:8000/
```

A página inicial (`index.html`) direciona para a Parte 1 ou Parte 2.

---

## Exemplos via CLI

```bash
# Parte 1 — BFS a partir de Recife
python -m src.cli --dataset ./data/aeroportos_data.csv --alg BFS --source REC --out ./out/

# Parte 1 — Dijkstra de Recife até Porto Alegre
python -m src.cli --dataset ./data/aeroportos_data.csv --alg DIJKSTRA --source REC --target POA --out ./out/

# Parte 2 — Dijkstra entre dois filmes
python -m src.cli --dataset ./data/dataset_parte2/ --alg DIJKSTRA --source "Jurassic Park" --target "Pulp Fiction" --out ./out/
```

---

## Testes

```bash
python -m pytest -v
```

12 testes cobrindo:

- **BFS**: níveis corretos em grafo pequeno e componente isolada
- **DFS**: detecção de ciclo e classificação de arestas (tree/back/cross/forward)
- **Dijkstra**: caminho correto, ausência de caminho, rejeição de peso negativo
- **Bellman-Ford**: peso negativo sem ciclo (distâncias corretas) + ciclo negativo detectado
- **I/O**: carregamento de CSV de arestas

---

## Saídas geradas

Após rodar `python -m src.solve`, os seguintes arquivos são criados:

### Parte 1 (`out/`)

| Arquivo | Conteúdo |
|---|---|
| `global.json` | Ordem, tamanho e densidade do grafo |
| `regioes.json` | Métricas por região do Brasil |
| `graus.csv` | Grau de cada aeroporto |
| `ego_aeroportos.csv` | Ego-networks dos principais hubs |
| `rankings.json` | Aeroportos mais conectados |
| `distancias_rotas.csv` | Caminhos mínimos (Dijkstra) |
| `grafo_interativo.html` | Grafo completo navegável |
| `arvore_percurso.html` | Percurso REC → POA e MAO → GRU |
| `subgrafo_hubs.html` | Subgrafo dos hubs principais |
| `histograma.png` | Distribuição de graus |
| `ranking.png` | Ranking visual dos hubs |
| `regioes.png` | Comparação por região |

### Parte 2 (`out/` e `interface/`)

| Arquivo | Conteúdo |
|---|---|
| `out/parte2_report.json` | Resultados de todos os algoritmos + benchmark |
| `interface/assets/*.png` | Gráficos analíticos (distribuição, benchmark, etc.) |
| `interface/data/resumo_parte2.json` | Resumo leve para a interface |
| `interface/data/parte2_amostra.json` | Amostra visual do grafo |
| `interface/data/parte2_grafo.json` | Grafo completo (100k arestas) para modo avançado |

---

## Estrutura do projeto

```
projeto-grafos/
├── data/
│   ├── aeroportos_data.csv
│   ├── adjacencias_aeroportos.csv
│   ├── rotas.csv
│   └── dataset_parte2/
│       ├── Imdb_filmes.csv
│       ├── Imdb_arestas.csv
│       └── artificiais_bellman_ford/
│           ├── bf_validacao_sem_ciclo.csv
│           └── bf_validacao_com_ciclo.csv
├── interface/
│   ├── data/           ← JSONs gerados pelo pipeline
│   ├── assets/         ← PNGs gerados pelo pipeline
│   ├── lib/            ← vis-network (local, sem CDN)
│   ├── index.html
│   ├── parte1.html
│   ├── styles.css
│   └── app.js
├── out/                ← saídas geradas (recriadas pelo pipeline)
├── src/
│   ├── shared/         ← Graph, algoritmos, I/O compartilhados
│   ├── parte1/         ← métricas e visualizações da Parte 1
│   ├── parte2/         ← builders da interface da Parte 2
│   ├── solve.py        ← pipeline principal
│   ├── viz.py          ← gerador de PNGs
│   └── cli.py          ← interface de linha de comando
├── tests/
├── index.html          ← página de entrada (escolha Parte 1 ou Parte 2)
├── requirements.txt
└── README.md
```

---

## Modelagem — Parte 2 (IMDb)

| Propriedade | Valor |
|---|---|
| Vértices | 3.985 filmes |
| Arestas | 100.000 conexões |
| Tipo | Não-dirigido, ponderado |
| Componentes conexas | 7 (maior: 3.971 filmes) |
| Grau médio | 50,19 |

**Fórmula de peso:**

```
similaridade = (2 × atores em comum) + gêneros em comum
peso         = 1 / similaridade
```

Conexões mais fortes têm peso menor — o Dijkstra escolhe naturalmente caminhos por filmes mais parecidos.

---

## Observações

- `plotly` foi removido do `requirements.txt` — não é usado no projeto.
- `networkx` é usado internamente pelo `pyvis` (visualização), mas **não** para nenhum algoritmo — toda a lógica de BFS, DFS, Dijkstra e Bellman-Ford é implementação própria.
- O arquivo `interface/data/parte2_grafo.json` (~8 MB) está versionado para evitar que a professora precise rodar o pipeline completo apenas para ver a interface.
- O modo "grafo completo" na interface renderiza as 3.000 arestas mais fortes das 100.000 disponíveis para não travar o navegador. O roteamento filme × filme continua usando todas as 100.000.
