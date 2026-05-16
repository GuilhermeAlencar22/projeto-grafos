# Projeto de Grafos - Parte 2

Rede de filmes do IMDb modelada como grafo, com BFS, DFS, Dijkstra e Bellman-Ford implementados do zero e visualizacao web interativa.

**Relatorio tecnico detalhado da branch pre-merge (Parte 2):**
https://docs.google.com/document/d/1iRzc20usINSrlRvJHTN3PdxI0YTkbO0oMMhQkzxXky8/edit?usp=sharing

```text
3.985 filmes  ->  100.000 conexoes  ->  4 algoritmos  ->  interface web
```


---

## Sumario

1. [Quick start](#quick-start)
2. [Objetivo da branch](#objetivo-da-branch)
3. [Objetivo tecnico](#objetivo-tecnico)
4. [Dataset](#dataset)
5. [Modelagem do grafo](#modelagem-do-grafo)
6. [Regra de similaridade e peso](#regra-de-similaridade-e-peso)
7. [Algoritmos implementados](#algoritmos-implementados)
8. [Interface web](#interface-web)
9. [Fluxo de dados](#fluxo-de-dados)
10. [Saidas geradas](#saidas-geradas)
11. [Como executar](#como-executar)
12. [Estrutura do projeto](#estrutura-do-projeto)
13. [Problemas comuns](#problemas-comuns)

---

## Objetivo da branch

Esta branch concentra a estrutura e a logica principal da Parte 2 do projeto. O foco aqui e deixar o dataset tratado, os algoritmos, os relatorios, os graficos e uma interface basica funcionando de ponta a ponta.

A divisao em branches foi feita para facilitar e agilizar o trabalho do grupo: Parte 1 e Parte 2 podem ser avaliadas individualmente pela professora antes do merge. Depois desse check separado, as duas partes devem ser unidas para seguir com melhorias no projeto inteiro, incluindo ajustes de UX, acabamento visual, integracao final e demandas de AVD.

Por isso, a interface desta branch serve como base funcional da Parte 2. Ela ja mostra dados, resultados e grafos, mas o polimento final da experiencia fica para depois do merge com a Parte 1.

### Pontos deixados para depois do merge

- polimento visual da interface
- ajustes finos de usabilidade
- aplicar a parte das analises de AVD
- otimizacao final do modo de grafo completo - ponto critico


---

## Quick start

```powershell
cd caminho\para\projeto-grafos

# dependencias
python -m pip install -r requirements.txt

# pipeline completo (do zero)
python -m src.solve
python -m src.viz parte2
python -m src.parte2.build_interface_data
python -m src.parte2.build_interface_grafo

# servidor local
python -m http.server 8000 --bind 127.0.0.1
```

Abrir no navegador: `http://127.0.0.1:8000/interface/`

---

## Objetivo tecnico

A parte 2 modela uma rede de filmes do IMDb e aplica algoritmos de grafos sobre ela.

A ideia central:

- filmes sao vertices;
- uma aresta existe quando dois filmes compartilham atores ou generos;
- o peso da aresta e invertido: conexoes mais fortes tem custo menor;
- os algoritmos (BFS, DFS, Dijkstra, Bellman-Ford) rodam sobre essa estrutura.


---

## Dataset

Dois arquivos finais:

```text
data/dataset_parte2/Imdb_filmes.csv
data/dataset_parte2/Imdb_arestas.csv
```

### Imdb_filmes.csv (vertices)

```text
filme, ano, generos, nota, diretores
```

### Imdb_arestas.csv (arestas)

```text
filme1, filme2, qtd_atores_compartilhados, atores_compartilhados, generos_compartilhados, similaridade, peso
```

### Resumo numerico

| Metrica | Valor |
|---|---|
| Vertices (filmes) | 3.985 |
| Arestas (conexoes) | 100.000 |
| Tipo | nao direcionado |
| Peso | positivo |
| Componentes conexas | 7 |
| Maior componente | 3.971 filmes |

---

## Modelagem do grafo

O grafo e nao direcionado. Cada linha do CSV de arestas gera uma conexao nos dois sentidos na lista de adjacencia. O carregamento principal acontece em:

```text
src/graphs/io.py
```

---

## Regra de similaridade e peso

```text
similaridade = (2 x atores em comum) + generos em comum
peso = 1 / similaridade
```

Por que ator vale 2: compartilhar um ator e evidencia direta de elenco em comum. Genero e mais amplo (drama, acao, comedia conectam milhares de filmes).

Por que o peso e invertido: similaridade alta = conexao forte = custo baixo. Assim o Dijkstra escolhe caminhos passando por filmes mais relacionados.

---

## Algoritmos implementados

Todos em `src/graphs/algorithms.py`.

### BFS

Percorre o grafo por camadas a partir de um filme fonte. Mede alcance e numero de camadas dentro da componente.

### DFS

Percorre em profundidade. Usado nas mesmas fontes da BFS para comparar comportamento e confirmar presenca de ciclos.

### Dijkstra

Caminho minimo entre pares de filmes com pesos positivos. Encontra o caminho de menor custo total, nao o de menor numero de arestas.

### Bellman-Ford

Valida o comportamento com pesos negativos em dois grafos artificiais pequenos:

- caso sem ciclo negativo;
- caso com ciclo negativo detectado.

Os CSVs ficam em `data/dataset_parte2/artificiais_bellman_ford/`. O grafo IMDb principal nao e usado aqui porque seus pesos sao positivos.

---

## Benchmark

O benchmark mede o tempo de execucao dos algoritmos da Parte 2 e registra os resultados em `out/parte2_report.json`.

As medicoes incluem:

- BFS e DFS em 3 filmes de partida;
- Dijkstra em 5 pares origem-destino;
- Bellman-Ford nos 2 grafos artificiais de validacao;
- tempos usados para comparar busca, caminho minimo e comportamento com peso negativo.

Esses dados tambem alimentam a interface e os graficos de comparacao de desempenho.

---

## Interface web

Interface vanilla (HTML + CSS + JavaScript puro) em `interface/`. Sem build, sem framework.

### Modos do grafo

- **maior similaridade** - subgrafo com as conexoes mais fortes
- **top conexoes** - filmes com mais ligacoes (hubs)
- **BFS** - percurso por camadas
- **DFS** - percurso em profundidade
- **Dijkstra** - caminhos minimos visuais
- **Bellman-Ford** - validacao com pesos negativos
- **grafo completo** - 100.000 conexoes do dataset, carregado sob demanda em modo pesado

### Recursos

- autocomplete com todos os 3.985 titulos nas caixas de busca;
- rota filme x filme usando todas as 100.000 arestas reais (Dijkstra ou DFS);
- benchmark de tempo por algoritmo;
- graficos gerados pelo Python embutidos.

---

## Fluxo de dados

```text
   CSVs              src/                interface/data/         navegador
+---------+      +-----------+        +------------------+      +---------+
| filmes  |----->| solve.py  |------->| report.json      |----->|         |
| arestas |      | viz.py    |        | resumo.json     |      |  vis-   |
+---------+      | parte2/*  |        | amostra.json     |      | network |
                 +-----------+        | parte2_grafo.json |      |         |
                       |              +------------------+      +---------+
                       v
                  out/parte2/*.png  -->  interface/assets/
```

Cada script Python tem responsabilidade unica:

| Script | Gera |
|---|---|
| `src.solve` | `out/parte2_report.json` (algoritmos + benchmark) |
| `src.viz parte2` | PNGs em `out/parte2/` e `interface/assets/` |
| `src.parte2.build_interface_data` | resumo e amostra visual |
| `src.parte2.build_interface_amostra` | so a amostra visual |
| `src.parte2.build_interface_grafo` | grafo completo com layout pre-computado |

---

## Saidas geradas

```text
out/
  parte2_report.json         # report tecnico com todos os algoritmos
  parte2/                    # pngs canonicos (rubrica oficial)

interface/
  assets/                    # espelho dos pngs para o navegador
  data/
    resumo_parte2.json      # resumo para a tela de resultados
    parte2_amostra.json      # 3.985 filmes + amostra visual de arestas
    parte2_grafo.json        # 100.000 arestas com layout pre-computado
```

### Quando cada JSON carrega

| Arquivo | Tamanho | Carrega quando |
|---|---|---|
| `resumo_parte2.json` | leve | ao abrir a interface |
| `parte2_amostra.json` | medio | ao abrir a interface |
| `parte2_grafo.json` |  | so quando o usuario seleciona "grafo completo" |

O layout do grafo completo e calculado em Python por grau de cada no (hubs no centro, perifericos na borda). O browser recebe as coordenadas prontas e nao precisa rodar simulacao de fisica.

---

## Como executar

Sempre a partir da raiz do projeto:

```powershell
cd caminho\para\projeto-grafos
```

### Pipeline completo (do zero)

```powershell
python -m pip install -r requirements.txt
python -m src.solve                          # roda algoritmos + benchmark
python -m src.viz parte2                     # gera os PNGs
python -m src.parte2.build_interface_data    # resumo + amostra visual
python -m src.parte2.build_interface_grafo   # grafo completo com layout
```

### Atualizando so a interface

Quando os CSVs e o report ja existem:

```powershell
python -m src.parte2.build_interface_data
python -m src.parte2.build_interface_grafo
```

### Subir o servidor

```powershell
python -m http.server 8000 --bind 127.0.0.1
```

Acessar: `http://127.0.0.1:8000/interface/`

### Rodar os testes

```powershell
python -m pytest
```

---

## Estrutura do projeto

```text
projeto-grafos/
|-- data/
|   `-- dataset_parte2/
|       |-- Imdb_filmes.csv
|       |-- Imdb_arestas.csv
|       `-- artificiais_bellman_ford/
|-- interface/
|   |-- index.html
|   |-- styles.css
|   |-- app.js
|   |-- assets/                       # espelho dos pngs
|   `-- data/
|       |-- resumo_parte2.json
|       |-- parte2_amostra.json
|       `-- parte2_grafo.json
|-- out/
|   |-- parte2_report.json            # report tecnico oficial
|   `-- parte2/                       # pngs
|-- src/
|   |-- cli.py
|   |-- solve.py
|   |-- viz.py
|   |-- graphs/
|   |   |-- graph.py
|   |   |-- io.py
|   |   |-- algorithms.py
|   |   `-- analysis.py
|   `-- parte2/
|       |-- build_interface_data.py
|       |-- build_interface_amostra.py
|       |-- build_interface_grafo.py
|       |-- build_visualizations.py
|       `-- relatorio.py
|-- tests/
`-- README.md
```

---

## Problemas comuns

**A interface abre mas o grafo nao carrega.**
Verifique se os JSONs existem em `interface/data/`. Rode `python -m src.parte2.build_interface_data` se algum estiver faltando.

**O modo "grafo completo" nao abre, demora ou trava.**
Esse modo carrega 100.000 arestas e pode exigir mais do navegador. Primeiro verifique se `interface/data/parte2_grafo.json` existe. Se nao existir, rode `python -m src.parte2.build_interface_grafo`. A otimizacao final desse modo pesado fica para o merge do projeto e para a etapa de UX final; ate la, use os subgrafos leves como visualizacao principal.

**Comando python -m nao encontra o modulo.**
Voce nao esta na raiz do projeto. Rode `cd` para a pasta `projeto-grafos` antes.
