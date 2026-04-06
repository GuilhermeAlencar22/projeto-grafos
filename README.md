# Projeto Final — Rede de Aeroportos do Brasil + Algoritmos de Grafos

## 📌 Descrição
ste projeto tem como objetivo modelar, analisar e visualizar a rede de aeroportos do Brasil utilizando conceitos de **Teoria dos Grafos** e **Algoritmos Clássicos**. 

A rede foi construída a partir de um dataset real de aeroportos e enriquecida com conexões baseadas em **voos diretos reais**, permitindo análises estruturais complexas e simulações de rotas otimizadas.

O projeto está dividido em duas etapas:

* **Parte 1:** Modelagem, métricas fundamentais, algoritmos de busca/caminho mínimo e visualizações interativas.
* **Parte 2:** Extensão com novos datasets, algoritmos avançados (Bellman-Ford), análise de performance e robustez da rede.

## 👥 Equipe
- Guilherme Alencar Augusto Correa - gaac@cesar.school
- Rodrigo Lucena Cavalcanti - rlc2@cesar.school 
- Rodrigo Torres Galindo Filho - rtgf@cesar.school 
- Erick Acioli Belo - eab2@cesar.school
- João Marcelo Tavares Pereira Montenegro - jmtpm@cesar.school

---

## Modelagem do Problema

A rede foi estruturada seguindo os princípios matemáticos de grafos:

* **Nós (Vértices):** Cada aeroporto é um nó identificado pelo seu código **IATA** (ex: REC, GRU, POA).
* **Arestas:** Cada conexão representa um voo direto entre dois aeroportos.
* **Propriedades do Grafo:**
    * **Não direcionado:** Se existe voo de A para B, assume-se a rota de retorno B para A.
    * **Conectado:** Não existem aeroportos isolados na rede principal.
    * **Ponderado:** As conexões possuem custos baseados no tempo.

As conexões foram definidas com base na malha aérea real brasileira, respeitando a hierarquia de *hubs* (centros de distribuição), aeroportos regionais e periféricos.

---

## Pesos das Arestas

Para tornar a simulação realista, os pesos das arestas representam o **tempo estimado de voo direto** em horas.

**Modelo adotado:** `peso = tempo_de_voo`

* ✔ Apenas valores positivos (garante compatibilidade com Dijkstra).
* ✔ Proporcionalidade real baseada na distância e logística aérea.

---

## Métricas Calculadas

O projeto gera uma série de arquivos na pasta `out/` com os resultados das análises:

### Globais
Estatísticas sobre a conectividade total da rede (Ordem, Tamanho e Densidade).
* Arquivo: `out/global.json`

### Por Região
Análise de subgrafos induzidos pelas regiões geográficas do Brasil.
* Arquivo: `out/regioes.json`

### Ego-Networks
Métricas locais para cada aeroporto:
* Grau (número de conexões).
* Ordem e Tamanho da vizinhança.
* Densidade local.
* Arquivo: `out/ego_aeroportos.csv`

---

## Rankings e Distribuição

* **Graus:** Lista ordenada de conectividade.
* **Hubs:** Identificação dos aeroportos com maior impacto na rede.
* Arquivos: `out/graus.csv` e `out/rankings.json`

---

## Algoritmos Implementados

Um dos diferenciais deste projeto é a **implementação manual** (do zero) dos algoritmos, sem o uso de bibliotecas de grafos prontas:

1.  **BFS (Breadth-First Search):** Para exploração de níveis e caminhos mínimos em grafos não ponderados.
2.  **DFS (Depth-First Search):** Para verificação de conectividade e exploração profunda.
3.  **Dijkstra:** Para encontrar a rota mais rápida (menor peso) entre quaisquer dois aeroportos na rede ponderada.
4.  *(Em breve)* **Bellman-Ford:** Para análise de caminhos com suporte a diferentes tipos de restrições.

---

## Cálculo de Rotas (Dijkstra)

O sistema calcula o caminho de custo mínimo entre todos os pares possíveis de aeroportos.
* Arquivo: `out/distancias_rotas.csv`

**Exemplos de Saída:**
* `REC → POA` | Custo (Horas): **4.33**
* `MAO → GRU` | Custo (Horas): **3.75**

---

## Visualizações

### 1. Árvore de Percurso
Representação dos caminhos mínimos estruturada como árvore.
* **Destaques:** Rotas coloridas, nós proporcionais ao grau e tooltips.
* Arquivo: `out/arvore_percurso.html`

### 2. Grafo Interativo Completo
Visualização dinâmica utilizando `pyvis`.
* **Funcionalidades:** Busca de aeroportos, zoom, navegação e layout dinâmico para evitar sobreposição.
* Arquivo: `out/grafo_interativo.html`

### 3. Gráficos Analíticos
* **Histograma:** Distribuição de graus dos aeroportos (`out/histograma.png`).
* **Ranking:** Comparação visual dos principais aeroportos (`out/ranking.png`).
* **Regiões:** Distribuição da malha por região brasileira (`out/regioes.png`).

---

## ▶️ Como Executar

1. **Clonar o repositório:**
   ```bash
   git clone [https://github.com/seu-usuario/nome-do-repositorio.git](https://github.com/seu-usuario/nome-do-repositorio.git)
   cd nome-do-repositorio ```
2. **Criar e ativar ambiente virtual:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Linux/Mac
    # No Windows use: venv\Scripts\activate ```
3. **Instalar dependências**
    ```bash
    pip install -r requirements.txt ```
4. **Executar o projeto:**
    ```bash
    python src/solve.py ```

---

## 📌 Tecnologias Utilizadas

* **Python 3.11+**
* **Matplotlib:** Geração de gráficos e histogramas.
* **Pyvis:** Visualização de redes interativas em HTML.
* **Heapq:** Implementação eficiente da fila de prioridade para o algoritmo de Dijkstra.
* **Pytest:** Framework de testes automatizados para garantir a integridade dos algoritmos.

---

## 🚀 Parte 2



---

## 📊 Conclusão

Este projeto demonstra como a **Teoria dos Grafos** pode ser aplicada para resolver problemas logísticos complexos no mundo real. A rede construída revela a estrutura hierárquica da aviação brasileira, destacando a importância vital de grandes *hubs* para a conectividade nacional e permitindo a otimização de rotas com base em dados reais de tempo e distância.