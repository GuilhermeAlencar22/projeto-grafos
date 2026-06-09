# Projeto Final — Teoria dos Grafos

Implementação de BFS, DFS, Dijkstra e Bellman-Ford em Python puro (sem NetworkX ou igraph), aplicados sobre dois datasets:

- **Parte 1** — rede de aeroportos brasileiros
- **Parte 2** — rede de filmes do IMDb (3.899 filmes, 63.484 conexões por elenco)

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

## Requisitos

- Python 3.10 ou superior
- pip

---

## Instalação

```bash
# Clone o repositório
git clone <url-do-repositorio>
cd projeto-grafos

# Crie e ative o ambiente virtual
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt
```

---

## Como rodar

> Todos os comandos devem ser executados na **raiz do projeto**.

### 1. Rodar tudo (Parte 1 + Parte 2)

```bash
python -m src.solve
```

Executa os quatro algoritmos, gera o relatório JSON, os PNGs e os dados da interface.

### 2. Rodar só a Parte 1

```bash
python -m src.solve parte1
```

### 3. Rodar só a Parte 2

```bash
python -m src.solve parte2
```

### 4. Gerar os dados da interface (Parte 2)

Necessário se quiser atualizar os JSONs consumidos pela interface sem rodar o pipeline completo:

```bash
python -m src.parte2.build_interface_data
python -m src.parte2.build_interface_grafo
```

### 5. Gerar os gráficos analíticos (PNGs)

```bash
python -m src.parte1.viz parte2
```

### 6. Abrir a interface no navegador

Use o **Live Server** do VS Code apontando para a pasta `interface/`, ou suba um servidor HTTP simples:

```bash
# na raiz do projeto
python -m http.server 8000 --bind 127.0.0.1
```

Abrir: `http://127.0.0.1:8000/interface/`

---

## Testes

```bash
python -m pytest -v
```

13 testes cobrindo BFS, DFS, Dijkstra, Bellman-Ford e I/O.

---

## CLI — exemplos de uso

```bash
# Parte 1 — BFS a partir de Recife
python -m src.cli --dataset ./data/aeroportos_data.csv --alg BFS --source REC --out ./out/

# Parte 1 — Dijkstra de Recife até Porto Alegre
python -m src.cli --dataset ./data/aeroportos_data.csv --alg DIJKSTRA --source REC --target POA --out ./out/

# Parte 2 — Dijkstra entre dois filmes
python -m src.cli --dataset ./data/dataset_parte2/ --alg DIJKSTRA --source "Jurassic Park" --target "Pulp Fiction" --out ./out/
```

---

## Estrutura de pastas

```
projeto-grafos/
├── data/
│   ├── aeroportos_data.csv          ← dataset Parte 1
│   ├── adjacencias_aeroportos.csv
│   ├── rotas.csv
│   └── dataset_parte2/
│       ├── Imdb_filmes.csv          ← vértices (filmes)
│       ├── Imdb_arestas.csv         ← arestas (similaridade por elenco)
│       └── artificiais_bellman_ford/
│           ├── bf_validacao_sem_ciclo.csv
│           └── bf_validacao_com_ciclo.csv
├── interface/
│   ├── index.html                   ← interface Parte 2
│   ├── parte1.html                  ← interface Parte 1
│   ├── app.js
│   ├── styles.css
│   ├── lib/                         ← vis-network (local, sem CDN)
│   ├── assets/                      ← PNGs gerados pelo pipeline
│   └── data/                        ← JSONs gerados pelo pipeline
├── out/                             ← saídas geradas (recriadas pelo pipeline)
├── src/
│   ├── shared/                      ← Graph, algoritmos, I/O
│   ├── parte1/                      ← métricas e visualizações Parte 1
│   ├── parte2/                      ← builders da interface Parte 2
│   ├── solve.py                     ← pipeline principal
│   ├── viz.py                       ← atalho para geração de PNGs
│   └── cli.py                       ← interface de linha de comando
├── tests/
├── requirements.txt
└── README.md
```

---

## Modelagem — Parte 2

Dois filmes são conectados quando compartilham atores ou gêneros. A força da conexão é calculada pela similaridade:

```
similaridade = (2 × atores em comum) + gêneros em comum
peso         = 1 / similaridade
```

Atores valem mais que gêneros porque indicam ligação direta de elenco. O peso é invertido para que o Dijkstra encontre caminhos pelos filmes mais parecidos (menor peso = maior similaridade).

| Propriedade | Valor |
|---|---|
| Vértices | 3.899 filmes |
| Arestas | 63.484 conexões |
| Tipo | Não-dirigido, ponderado |
| Componentes | 1 (componente gigante) |
| Grau médio | 32,6 |
| Hub principal | The Royal Tenenbaums (grau 142) |

---

## Algoritmos

Todos implementados do zero, sem bibliotecas de grafos:

| Algoritmo | Dataset | O que demonstra |
|---|---|---|
| BFS | IMDb (3 fontes) | Percurso por camadas, alcance da componente |
| DFS | IMDb (3 fontes) | Percurso em profundidade, detecção de ciclos |
| Dijkstra | IMDb (5 pares) | Caminho mínimo ponderado entre filmes |
| Bellman-Ford | Grafos artificiais | Pesos negativos sem ciclo + detecção de ciclo negativo |

O Bellman-Ford roda em grafos artificiais porque o grafo IMDb tem apenas pesos positivos. Os dois CSVs de validação estão em `data/dataset_parte2/artificiais_bellman_ford/`.
