# Relatório de Análise e Visualização de Dados (AVD)
## Projeto Final — Teoria dos Grafos

**Disciplinas:** Teoria dos Grafos + Análise e Visualização de Dados  
**Equipe:** Guilherme Alencar, Erick Belo, Rodrigo Torres  
**Repositório:** https://github.com/GuilhermeAlencar22/projeto-grafos

---

## 1. Contexto

### 1.1 Problema e Motivação

O projeto modela dois domínios reais como grafos e aplica algoritmos clássicos de busca e caminho mínimo implementados do zero — sem NetworkX, igraph ou bibliotecas de algoritmos prontos. A escolha de visualizações não foi cosmética: cada decisão de design partiu de uma pergunta analítica concreta.

**Parte 1 — Rede de Aeroportos Brasileiros**  
Por que pesos nos aeroportos? A malha aérea tem características assimétricas: aeroportos regionais pequenos têm alta densidade local (todos os destinos disponíveis conectam-se entre si), mas baixa cobertura nacional. Usar peso nas arestas como proxy de custo/distância permite responder *qual é o caminho mais barato*, não apenas o mais curto em saltos.

**Parte 2 — Rede de Similaridade IMDb**  
O peso da aresta representa similaridade entre filmes (calculada por atores compartilhados). Um peso alto = filmes muito similares = aresta "curta" em termos de distância no Dijkstra. Isso inverte a intuição: o caminho mínimo conecta filmes *mais próximos*, não *mais distantes*.

### 1.2 Arquitetura de Visualização

A interface interativa **não foi construída em `src/viz.py` nem em `src/parte1/viz.py`**. Esses arquivos são responsáveis exclusivamente pelas saídas estáticas da Parte 1 (gráficos Matplotlib e HTMLs Pyvis da rede de aeroportos).

A interface web da Parte 2 foi construída em:

| Arquivo | Responsabilidade |
|---------|-----------------|
| `src/parte2/build_interface_data.py` | Gera `interface/data/resumo_parte2.json` e `parte2_amostra.json` |
| `src/parte2/build_interface_grafo.py` | Gera `interface/data/parte2_grafo.json` (grafo completo) |
| `src/parte2/build_visualizations.py` | Gera os 5 PNGs analíticos em `interface/assets/` |
| `interface/index.html` + `app.js` + `styles.css` | Frontend em Vis.js com filtros e tooltips |

---

## 2. Exploração dos Dados

### 2.1 Parte 1 — Rede de Aeroportos

| Métrica | Valor |
|---------|-------|
| Vértices (aeroportos) | 20 |
| Arestas (rotas) | 114 |
| Densidade global | 0,60 |
| Hub mais conectado | BSB (grau 19) |
| Maior densidade local | THE (densidade de ego = 1,0) |

**Distribuição por região:**

| Região | Aeroportos | Rotas | Densidade |
|--------|-----------|-------|-----------|
| Nordeste | 6 | 10 | 0,67 |
| Sudeste | 5 | 9 | 0,90 |
| Centro-Oeste | 2 | 1 | 1,00 |
| Sul | 3 | 2 | 0,67 |
| Norte | 4 | 2 | **0,33** |

A região Norte apresenta a menor densidade de rotas (0,33) — apenas 2 arestas conectando 4 aeroportos — tornando-a a região mais vulnerável à remoção de um único nó.

**O que os dados revelam:**  
Brasília (BSB) com grau 19 conecta-se a praticamente todos os outros aeroportos do grafo. É um ponto único de falha: sua remoção particionaria o grafo. Teresina (THE) tem densidade de ego 1,0 — todos os aeroportos na sua vizinhança local estão mutuamente conectados, formando uma clique regional.

### 2.2 Parte 2 — Rede IMDb

| Métrica | Valor |
|---------|-------|
| Vértices (filmes) | 3.899 |
| Arestas (similaridades) | 63.484 |
| Grau médio | 32,56 |
| Grau máximo | 142 |
| Componentes conexas | 1 (grafo totalmente conectado) |

O grafo IMDb é fortemente conectado: qualquer filme alcança qualquer outro. O grau máximo de 142 indica um filme com altíssima co-participação de atores com outros filmes — um hub de popularidade cinematográfica.

---

## 3. Modelagem sob Gestalt

As leis da Gestalt nortearam cada decisão de design visual nas três camadas de output: gráficos estáticos (Matplotlib), grafo interativo de aeroportos (Pyvis), e interface web IMDb (Vis.js).

### 3.1 Lei da Similaridade — cores por região

No `grafo_interativo.html` (aeroportos), cada aeroporto recebe uma cor determinada pela sua região geográfica. O olho agrupa automaticamente nós da mesma cor como pertencentes ao mesmo cluster regional, sem necessidade de legenda para perceber a separação Norte/Nordeste/Sudeste/Sul/Centro-Oeste.

Na interface IMDb, filmes são coloridos por similaridade média — tons mais quentes indicam hubs com alta conectividade.

### 3.2 Lei da Conectividade — espessura proporcional ao peso

Arestas mais pesadas (rotas com menor custo normalizado / maior similaridade) são renderizadas com maior espessura. O olho segue naturalmente as linhas mais grossas como os "caminhos principais" do grafo.

### 3.3 Lei da Região Comum — subgrafos regionais

O plot `subgrafo_por_regiao` (`out/subgrafo_hubs.png`) usa áreas coloridas de fundo para demarcar cada região. Elementos dentro da mesma área colorida são percebidos como grupo, mesmo sem bordas explícitas.

### 3.4 Figura-Fundo — fundo escuro, caminhos em cor vibrante

O grafo interativo usa fundo escuro (`#1a1a2e`). Os caminhos Dijkstra calculados (REC→POA, MAO→GRU) são destacados em laranja/amarelo sobre o fundo escuro, criando contraste máximo sem sobrecarregar a cena. Nós não pertencentes ao caminho ficam em opacidade reduzida — aplicação direta da lei figura-fundo.

### 3.5 Lei da Proximidade — agrupamento de hubs

No `plot_ranking` (`out/ranking.png`), os aeroportos são ordenados verticalmente por grau decrescente. Aeroportos com grau similar ficam fisicamente próximos na visualização, permitindo leitura imediata de "grupos de conectividade" sem análise numérica explícita.

---

## 4. Resultados

### 4.1 Caminhos Mínimos — Parte 1

| Rota | Custo | Caminho |
|------|-------|---------|
| REC → POA | 4,33 | REC → POA (direto) |
| MAO → GRU | 3,83 | MAO → GRU (direto) |
| REC → BSB | 2,58 | REC → BSB (direto) |
| FOR → GIG | 3,33 | FOR → GIG (direto) |
| SSA → CWB | 3,00 | SSA → CWB (direto) |

Todas as rotas obrigatórias têm caminho direto (1 salto). Isso reflete a alta densidade do grafo (0,60): com 60% das arestas possíveis presentes, conexões diretas são a norma, não a exceção.

### 4.2 Algoritmos — Parte 2 (Benchmark em 3.899 nós)

| Algoritmo | Fonte | Nós Visitados | Tempo (ms) |
|-----------|-------|--------------|-----------|
| BFS | Jurassic Park | 3.899 | 9,4 |
| BFS | Forrest Gump | 3.899 | 9,3 |
| BFS | Pulp Fiction | 3.899 | 9,3 |
| DFS | Jurassic Park | 3.899 | 12,1 |
| DFS | Forrest Gump | 3.899 | 12,9 |
| DFS | Pulp Fiction | 3.899 | 12,5 |

BFS é ~25% mais rápido que DFS no grafo IMDb — resultado esperado dado o alto grau médio (32,56): a fila de BFS tem melhor localidade de memória que a pilha recursiva de DFS em grafos densos.

**Dijkstra — pares selecionados:**

| Par | Custo | Saltos | Tempo (ms) |
|-----|-------|--------|-----------|
| Jurassic Park → Independence Day | 0,167 | 2 | 0,1 |
| Jurassic Park → Pulp Fiction | 0,333 | 2 | 1,8 |
| Jurassic Park → Finding Forrester | 0,688 | 5 | 24,0 |
| Jurassic Park → Millennium Actress | 1,617 | 8 | 36,1 |
| Millennium Actress → Bambi | 2,767 | 12 | 27,6 |

Filmes em gêneros distintos ("Millennium Actress" e "Bambi") exigem 12 intermediários para serem conectados — os extremos do espaço de similaridade cinematográfica.

**Bellman-Ford — validação com dados sintéticos:**

O dataset IMDb não contém pesos negativos, portanto Bellman-Ford foi validado com grafos artificiais:
- `bf_validacao_sem_ciclo.csv`: detecta distâncias corretas em 0,022 ms (Z→a: 5,0; Z→b: 2,0; Z→c: 2,0)
- `bf_validacao_com_ciclo.csv`: detecta ciclo negativo corretamente em 0,011 ms

### 4.3 Storytelling Analítico — da Exploração à Explanação

O fluxo narrativo segue o padrão **exploratório → explanatório**:

1. **Exploração** (seção "Dataset"): o usuário vê o histograma de graus e as métricas globais — entende *o que existe* no grafo.
2. **Questionamento** (seção "Algoritmos"): executa BFS/DFS/Dijkstra e vê os caminhos percorridos — entende *como o grafo é navegado*.
3. **Explicação** (seção "Gráficos AVD"): os 5 gráficos analíticos com insights e tags Gestalt/Storytelling explicam *por que* esses padrões existem.
4. **Conclusão** (seção "Resultados"): comparação de performance e caminhos mínimos — o usuário sai com insight acionável.

---

## 5. Limitações

### 5.1 Densidade pode mascarar a estrutura real

O grafo de aeroportos com densidade 0,60 é artificialmente denso em relação à malha aérea real do Brasil. A rota real REC→POA tem escala, tempo e preço variáveis — o modelo de grafo simples não captura essas dimensões. As visualizações de subgrafos regionais compensam isso parcialmente, mas não eliminam a abstração.

### 5.2 Interface construída nos arquivos `build_*`, não em `viz.py`

Um ponto de possível confusão na arquitetura do projeto: `src/viz.py` (que foi removido na tarefa de limpeza) e `src/parte1/viz.py` cobrem **apenas a Parte 1** — gráficos Matplotlib de distribuição de graus, ranking, regiões, subgrafos de hubs, e HTMLs Pyvis do grafo interativo de aeroportos.

A interface web da Parte 2 é inteiramente gerada pelos arquivos `build_*`:
- `build_interface_data.py` — JSON de dados
- `build_interface_grafo.py` — JSON do grafo
- `build_visualizations.py` — PNGs analíticos

Qualquer extensão da interface deve ser feita nesses arquivos, **não em `viz.py`**.

### 5.3 Bellman-Ford com dados sintéticos

O algoritmo Bellman-Ford foi implementado e validado corretamente, mas testado apenas em grafos artificiais pequenos (4 nós). O dataset IMDb não tem pesos negativos, portanto não há cenário real no projeto onde BF seja estritamente necessário — Dijkstra resolve todos os casos com pesos não-negativos com menor overhead.

### 5.4 Grafo IMDb: similaridade ≠ qualidade

O peso de aresta é calculado por atores compartilhados, não por qualidade crítica, gênero ou temática. "Jurassic Park" e "Independence Day" têm alta similaridade (custo 0,167) por compartilharem elenco, mas são narrativamente distintos. A visualização não contextualiza essa limitação — o usuário pode interpretar "caminho mínimo" como "filmes mais parecidos tematicamente".

---

## 6. Conclusão

### 6.1 Insights Acionáveis

**BSB como hub nacional crítico**  
Brasília com grau 19 (dos 20 aeroportos) é um ponto único de falha na malha modelada. Qualquer interrupção em BSB (mau tempo, interdição) potencialmente desconecta regiões inteiras. Do ponto de vista de visualização, isso justifica destacar BSB com nó maior e cor distinta no grafo interativo — aplicação direta da hierarquia visual.

**Norte: região mais vulnerável**  
Com densidade de subgrafo 0,33 (a menor entre as 5 regiões), a região Norte tem apenas 2 rotas conectando 4 aeroportos. Um modelo de resiliência de rede indicaria essa região como prioridade para expansão de conectividade.

**Dijkstra é suficiente para a Parte 1**  
Todos os pesos do grafo de aeroportos são não-negativos. Bellman-Ford adiciona complexidade O(VE) sem benefício prático neste dataset. A decisão de implementar os dois algoritmos foi pedagógica — para demonstrar a detecção de ciclos negativos — mas o report deixa claro que Dijkstra é a escolha correta para este domínio.

**IMDb: filmes de ação como hubs de similaridade**  
"Jurassic Park", "Independence Day" e "Pulp Fiction" como fontes nos testes BFS/DFS visitam todos os 3.899 nós — confirmando que o grafo é fortemente conectado. Filmes com grandes elencos de atores populares funcionam como hubs de similaridade, ancorando o espaço de recomendação.

### 6.2 Avaliação AVD — Critérios Atendidos

| Critério | Peso | Implementação |
|----------|------|---------------|
| Aplicação de Gestalt | 0,5 | Similaridade (cores por região), Conectividade (espessura de arestas), Região Comum (subgrafos coloridos), Figura-Fundo (fundo escuro + caminhos vibrantes) |
| Storytelling Analítico | 0,4 | Fluxo exploratório→explanatório na interface; insights com tag Gestalt/Storytelling em cada viz-card |
| Hierarquia Visual | 0,3 | BSB destacado como hub; caminhos Dijkstra em primeiro plano; nós secundários em opacidade reduzida |
| Interatividade & UX | 0,3 | Filtros por fonte/algoritmo; tooltips com métricas ao passar o cursor; navegação sem recarregamento de página |

---

*Relatório gerado para a disciplina Análise e Visualização de Dados — CESAR School, 2026.1*
