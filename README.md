# projeto-grafos

## Trabalho de grafos em Python com dataset IMDb.
- git provisorio 

#### 👥 Equipe
- Guilherme Alencar Augusto Correa - gaac@cesar.school
- Rodrigo Lucena Cavalcanti - rlc2@cesar.school 
- Rodrigo Torres Galindo Filho - rtgf@cesar.school 
- Erick Acioli Belo - eab2@cesar.school
- João Marcelo Tavares Pereira Montenegro - jmtpm@cesar.school

## Como Rodar
```bash
pip install -r requirements.txt
python src/solve.py
python src/solve.py --rapido
```

`--rapido` roda so check, bfs e dfs (pula tres_fontes, dijkstra e bellman_ford).

### Estrutura
O fluxo atualiza `out/parte2_report.json`. Pra gerar os png em `out/`, roda `python src/parte2/build_visualizations.py` quando precisar.
