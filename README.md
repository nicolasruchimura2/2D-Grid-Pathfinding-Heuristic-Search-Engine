# Planeamento de trajetos em grelha 2D com custos variáveis

Projeto Prático 2 de Inteligência Artificial (90498), ESTGA.
Dijkstra, A* e Weighted A* implementados de raiz, em Python, sobre uma grelha com custos de entrada de 1 a 9 e obstáculos.

## Requisitos

- Python ≥ 3.10.
- O motor de pesquisa (`pathfinding/`) e os testes usam só a biblioteca padrão.
- As figuras precisam de `matplotlib` e `numpy`:

```bash
pip install -r requirements.txt
```

## Utilização

```bash
python gerar_cenarios.py        # (re)gera os 6 cenários do grupo em cenarios/ (semente 42)
python -m unittest -v           # testes
python experiencias.py          # todas as experiências -> resultados/ e figuras/ (~15 s)
python planear.py cenarios/F_terrenos_40x40.txt --alg astar --mov 8
```

Opções de `planear.py`: `--alg dijkstra|astar`, `--heur manhattan|euclidiana|octile`, `--mov 4|8`,
`--w <peso>` (Weighted A*), `--desempate fifo|h` e `--sem-mapa`.

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `pathfinding/grelha.py` | leitura dos mapas, vizinhos em 4/8 direções, regra de não cortar esquinas |
| `pathfinding/heuristicas.py` | Manhattan, Euclidiana e Octile |
| `pathfinding/pesquisa.py` | função única `pesquisar()`: Dijkstra (sem h), A* (w = 1) e Weighted A* (w > 1) |
| `gerar_cenarios.py` | geradores determinísticos dos cenários D–I |
| `experiencias.py` | medições, CSVs, tabelas e figuras |
| `planear.py` | CLI para um mapa individual |
| `tests/` | testes unitários e de propriedades (otimalidade, limite w·C*, validade dos caminhos) |
| `cenarios/` | mapas em texto |
| `resultados/` | `comparacao.csv`, `desempate.csv`, `weighted.csv`, `escalabilidade.csv`, `tabelas.md` |
| `figuras/` | gráficos do relatório e mapas com os caminhos e os nós expandidos |
| `relatorio/RELATORIO.md` | texto do relatório com os resultados |

## Formato dos mapas

```
S..#....
.3.#.88.
...#..#G
```

`S` início, `G` objetivo, `#` obstáculo, `.` custo 1, `1`–`9` custo de entrada.
As células podem estar separadas por espaços.
As linhas começadas por `;` são comentários.

## Cenários

| Ficheiro | Dimensão | Objetivo do cenário |
|---|---|---|
| `A_labirinto_7x10.txt` | 7×10 | Anexo A (validação) |
| `B_terrenos_5x9.txt` | 5×9 | Anexo A (validação) |
| `C_sem_caminho_4x6.txt` | 4×6 | Anexo A (validação) |
| `D_labirinto_61x61.txt` | 61×61 | labirinto com ciclos (10% das paredes interiores removidas) |
| `E_aberto_120x120.txt` | 120×120 | espaço aberto, 5% de obstáculos, custo uniforme |
| `F_terrenos_40x40.txt` | 40×40 | o caminho com menos passos atravessa um pântano (7–9); o ótimo contorna-o por uma estrada |
| `G_obstaculo_U_60x60.txt` | 60×60 | obstáculo côncavo virado para S (armadilha para a heurística) |
| `H_aleatorio_80x80.txt` | 80×80 | 28% de obstáculos e custos aleatórios de 1 a 9 |
| `I_sem_caminho_100x100.txt` | 100×100 | G fechado num anel de obstáculos: provar que não há caminho |

## Decisões de implementação

- O teste de objetivo é feito quando o nó sai da fronteira, não quando é gerado. É isso que garante a otimalidade.
- A fronteira é um `heapq` com eliminação preguiçosa: as entradas obsoletas são ignoradas ao sair.
- O desempate por omissão é FIFO (contador de inserção).
  A opção `desempate="h"` prefere o menor h em caso de empate em f, o que reduz muito os nós expandidos em zonas de custo uniforme (ver `resultados/tabelas.md`).
- As comparações de g usam uma tolerância de 1e-9.
  Sem ela, somas com √2 feitas por ordens diferentes geram "melhorias" de ~1e-16 e reaberturas espúrias.
- O Weighted A* reabre nós fechados por omissão (`reabrir=True` quando w > 1).
  `experiencias.py` mede também a variante sem reabertura.
