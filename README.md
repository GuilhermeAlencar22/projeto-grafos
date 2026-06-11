# Projeto Final — Teoria dos Grafos

Implementação de BFS, DFS, Dijkstra e Bellman-Ford em Python puro (sem NetworkX ou igraph), aplicados sobre dois datasets:

- **Parte 1** — rede de aeroportos brasileiros
- **Parte 2** — rede de filmes do IMDb (3.899 filmes, 63.484 conexões por elenco)

---

## Documentação

- [Relatório Técnico](PROJETO%20FINAL%20—%20TEORIA%20DOS%20GRAFOS.pdf)
- [Relatório AVD](relatorio_avd.md)
- [Slides de Apresentação](Apresentacao_Grafos.pdf)

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

## Como rodar (do zero)

Execute os passos abaixo **na ordem**. Todos os comandos devem ser executados na **raiz do projeto**.

### Passo 1 — Clonar e configurar o ambiente

```bash
git clone <url-do-repositorio>
cd projeto-grafos

python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

### Passo 2 — Gerar todos os dados e relatórios

Este comando executa os quatro algoritmos, gera o relatório JSON e os gráficos PNG:

```bash
python -m src.solve
```

### Passo 3 — Gerar os arquivos da interface web

Este comando cria os JSONs que a interface consome. **Sem ele, a interface abre vazia:**

```bash
python -m src.parte2.build_interface_data
python -m src.parte2.build_interface_grafo
```

### Passo 4 — Subir o servidor e abrir no navegador

```bash
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

## Comandos adicionais

Úteis para rodar partes específicas sem refazer tudo.

### Rodar só a Parte 1

```bash
python -m src.solve parte1
```

### Rodar só a Parte 2

```bash
python -m src.solve parte2
```

### CLI — exemplos de uso direto

```bash
# BFS a partir de Recife (Parte 1)
python -m src.cli --dataset ./data/aeroportos_data.csv --alg BFS --source REC --out ./out/

# Dijkstra de Recife até Porto Alegre (Parte 1)
python -m src.cli --dataset ./data/aeroportos_data.csv --alg DIJKSTRA --source REC --target POA --out ./out/

# Dijkstra entre dois filmes (Parte 2)
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
