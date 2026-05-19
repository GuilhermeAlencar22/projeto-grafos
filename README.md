# Projeto Final - Rede de Aeroportos + IMDb

Projeto final de Teoria dos Grafos, dividido em duas partes: modelagem da rede de aeroportos do Brasil e comparacao de algoritmos em um dataset maior de filmes do IMDb.

O projeto usa implementacao propria dos algoritmos de grafo. Nao foram usadas bibliotecas prontas de grafos para BFS, DFS, Dijkstra ou Bellman-Ford.

## Sumario

1. [Equipe](#equipe)
2. [Visao geral](#visao-geral)
3. [Parte 1 - Aeroportos](#parte-1---aeroportos)
4. [Parte 2 - IMDb](#parte-2---imdb)
5. [Algoritmos](#algoritmos)
6. [Saidas geradas](#saidas-geradas)
7. [Como executar](#como-executar)
8. [Interface](#interface)
9. [Testes](#testes)
10. [Estrutura](#estrutura)
11. [Observacoes](#observacoes)

## Equipe

- Guilherme Alencar Augusto Correa - gaac@cesar.school
- Rodrigo Lucena Cavalcanti - rlc2@cesar.school
- Rodrigo Torres Galindo Filho - rtgf@cesar.school
- Erick Acioli Belo - eab2@cesar.school
- Joao Marcelo Tavares Pereira Montenegro - jmtpm@cesar.school

## Visao geral

A Parte 1 modela uma rede de aeroportos brasileiros. Cada aeroporto e um vertice, e cada conexao representa uma rota direta definida pelo grupo.

A Parte 2 usa um dataset maior baseado em filmes do IMDb. Cada filme e um vertice, e as arestas representam conexoes entre filmes por atores e generos compartilhados.

As duas partes usam a mesma base de estrutura de grafo e os mesmos algoritmos principais, mantendo a separacao dos dados e das geracoes especificas.

## Parte 1 - Aeroportos

Dataset principal:

- `data/aeroportos_data.csv`
- `data/adjacencias_aeroportos.csv`
- `data/rotas.csv`

Modelagem:

- vertices: aeroportos identificados por codigo IATA;
- arestas: conexoes entre aeroportos;
- grafo: nao direcionado, conectado e ponderado;
- peso: tempo estimado de voo direto.

A Parte 1 calcula metricas globais, metricas por regiao, ego-networks, graus, rankings e rotas minimas com Dijkstra.

## Parte 2 - IMDb

Dataset final:

- `data/dataset_parte2/Imdb_filmes.csv`
- `data/dataset_parte2/Imdb_arestas.csv`

Casos artificiais do Bellman-Ford:

- `data/dataset_parte2/artificiais_bellman_ford/bf_validacao_sem_ciclo.csv`
- `data/dataset_parte2/artificiais_bellman_ford/bf_validacao_com_ciclo.csv`

Modelagem:

- vertices: filmes;
- arestas: pares de filmes conectados por atores ou generos em comum;
- grafo IMDb: nao direcionado e ponderado;
- Bellman-Ford: usa grafos dirigidos artificiais para validar pesos negativos e ciclo negativo.

Metricas atuais da Parte 2:

- vertices: 3.985 filmes;
- arestas: 100.000 conexoes;
- componentes conexas: 7;
- maior componente: 3.971 vertices;
- maior grau: `True Romance`, grau 208.

Regra de similaridade:

```text
similaridade = (2 * atores em comum) + generos em comum
peso = 1 / similaridade
```

Quanto maior a similaridade entre dois filmes, menor o peso da aresta. Assim, o Dijkstra prefere caminhos com conexoes mais fortes.

Relatorio tecnico detalhado da branch pre-merge da Parte 2:

https://docs.google.com/document/d/1iRzc20usINSrlRvJHTN3PdxI0YTkbO0oMMhQkzxXky8/edit?usp=sharing

## Algoritmos

Algoritmos implementados manualmente:

- BFS: busca em largura, usada para alcance, visitados e camadas;
- DFS: busca em profundidade, usada para exploracao e ciclos;
- Dijkstra: menor caminho com pesos nao negativos;
- Bellman-Ford: pesos negativos e deteccao de ciclo negativo.

Na Parte 2:

- BFS e DFS rodam em 3 fontes distintas;
- Dijkstra roda em pelo menos 5 pares origem-destino;
- Bellman-Ford roda em um caso com peso negativo sem ciclo negativo e outro com ciclo negativo detectado;
- tempos de execucao sao registrados em `out/parte2_report.json`.

## Saidas geradas

Parte 1:

- `out/global.json`
- `out/regioes.json`
- `out/ego_aeroportos.csv`
- `out/graus.csv`
- `out/rankings.json`
- `out/distancias_rotas.csv`
- `out/arvore_percurso.html`
- `out/grafo_interativo.html`
- `out/histograma.png`
- `out/ranking.png`
- `out/regioes.png`
- `out/subgrafo_hubs.html`

Parte 2:

- `out/parte2_report.json`
- `out/parte2/parte2_benchmark_tempos.png`
- `out/parte2/parte2_distribuicao_graus.png`
- `out/parte2/parte2_componentes_conexas.png`
- `out/parte2/parte2_similaridade_vs_peso.png`
- `out/parte2/parte2_atores_vs_similaridade.png`
- `interface/data/resumo_parte2.json`
- `interface/data/parte2_amostra.json`
- `interface/data/parte2_grafo.json`

## Como executar

Instalar dependencias:

```powershell
python -m pip install -r requirements.txt
```

Rodar tudo:

```powershell
python -m src.solve
```

Rodar apenas a Parte 1:

```powershell
python -m src.solve parte1
```

Rodar apenas a Parte 2:

```powershell
python -m src.solve parte2
```

Gerar visualizacoes da Parte 2:

```powershell
python -m src.viz parte2
```

Gerar dados da interface da Parte 2:

```powershell
python -m src.parte2.build_interface_data
python -m src.parte2.build_interface_grafo
```

Rodar servidor local:

```powershell
python -m http.server 8000 --bind 127.0.0.1
```

Abrir:

```text
http://127.0.0.1:8000/
```

## Interface

A interface principal fica em:

- `index.html`
- `interface/parte1.html`
- `interface/index.html`
- `interface/styles.css`
- `interface/app.js`

Ela usa HTML, CSS e JavaScript puro com `vis-network` para os grafos interativos.

Na raiz do projeto, `index.html` serve como entrada simples para escolher Parte 1 ou Parte 2.

Na Parte 1, `interface/parte1.html` organiza os arquivos gerados em `out/`, incluindo grafo interativo, arvore de percurso, subgrafo de hubs e graficos analiticos.

Na Parte 2, a interface mostra:

- resumo do dataset;
- subgrafos visuais;
- busca e rotas entre filmes;
- resultados dos algoritmos;
- graficos de desempenho e estrutura.

O modo de grafo completo carrega um arquivo maior (`parte2_grafo.json`) e pode exigir mais do navegador. O refinamento final desse modo fica para a etapa de acabamento apos o merge.

## Testes

Rodar testes:

```powershell
python -m pytest -q
```

Testes cobrem:

- BFS com visitados e niveis;
- DFS simples e classificacao de arestas;
- Dijkstra com caminho, ausencia de caminho e rejeicao de peso negativo;
- Bellman-Ford com peso negativo sem ciclo negativo e ciclo negativo detectado;
- loader de CSV de arestas.

## Estrutura

```text
projeto-grafos/
├─ data/
│  ├─ aeroportos_data.csv
│  ├─ adjacencias_aeroportos.csv
│  ├─ rotas.csv
│  └─ dataset_parte2/
├─ interface/
│  ├─ data/
│  ├─ assets/
│  ├─ index.html
│  ├─ styles.css
│  └─ app.js
├─ out/
├─ src/
│  ├─ graphs/
│  ├─ parte2/
│  ├─ utils/
│  ├─ cli.py
│  ├─ solve.py
│  └─ viz.py
├─ tests/
├─ requirements.txt
└─ README.md
```

## Observacoes

- A branch de teste de merge junta a Parte 1 e a Parte 2 para validacao antes de aplicar na `main`.
- A Parte 1 continua focada na rede de aeroportos.
- A Parte 2 continua focada no dataset IMDb e na comparacao de algoritmos.
- As melhorias finais de UX, AVD e acabamento visual devem ser feitas depois da validacao do merge.
