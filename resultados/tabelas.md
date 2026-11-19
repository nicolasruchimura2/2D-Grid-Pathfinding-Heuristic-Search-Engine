# Tabelas geradas por experiencias.py

## Validação (Anexo A)

| Cenário | Custo 4 dir. (esperado → obtido) | Custo 8 dir. (esperado → obtido) | Nós 4 dir. Dijkstra / A* Manhattan |
|---|---|---|---|
| A_labirinto_7x10 | 17,00 → 17,00 ✔ | 17,00 → 17,00 ✔ | 35 / 27 |
| B_terrenos_5x9 | 20,00 → 20,00 ✔ | 18,83 → 18,83 ✔ | 30 / 29 |
| C_sem_caminho_4x6 | sem caminho → sem caminho ✔ | sem caminho → sem caminho ✔ | 6 / 6 |

## Dijkstra vs. A* (4 direções, Manhattan)

| Cenário | Dijkstra: custo / nós / tempo (ms) | A*: custo / nós / tempo (ms) | Ganho em nós | Ganho em tempo |
|---|---|---|---|---|
| A_labirinto_7x10 | 17,00 / 35 / 0,03 | 17,00 / 27 / 0,03 | 22,9% | 8,8% |
| B_terrenos_5x9 | 20,00 / 30 / 0,03 | 20,00 / 29 / 0,04 | 3,3% | -15,2% |
| C_sem_caminho_4x6 | sem caminho / 6 / 0,01 | sem caminho / 6 / 0,01 | 0,0% | -25,0% |
| D_labirinto_61x61 | 152,00 / 1805 / 1,94 | 152,00 / 692 / 0,87 | 61,7% | 55,0% |
| E_aberto_120x120 | 184,00 / 13299 / 20,75 | 184,00 / 7835 / 12,15 | 41,1% | 41,4% |
| F_terrenos_40x40 | 71,00 / 837 / 1,11 | 71,00 / 304 / 0,51 | 63,7% | 54,5% |
| G_obstaculo_U_60x60 | 77,00 / 3443 / 4,52 | 77,00 / 1683 / 2,47 | 51,1% | 45,4% |
| H_aleatorio_80x80 | 648,00 / 4535 / 5,58 | 648,00 / 4535 / 6,27 | 0,0% | -12,4% |
| I_sem_caminho_100x100 | sem caminho / 8976 / 12,03 | sem caminho / 8976 / 14,44 | 0,0% | -20,1% |

## Heurísticas e modelos de movimento (nós expandidos; custo se subótimo)

| Cenário | Mov. | Dijkstra | Manhattan | Euclidiana | Octile |
|---|---|---|---|---|---|
| A_labirinto_7x10 | 4 | 35 | 27 | 27 | 27 |
| A_labirinto_7x10 | 8 | 35 | 27 | 27 | 27 |
| B_terrenos_5x9 | 4 | 30 | 29 | 29 | 29 |
| B_terrenos_5x9 | 8 | 30 | 25 | 28 | 28 |
| C_sem_caminho_4x6 | 4 | 6 | 6 | 6 | 6 |
| C_sem_caminho_4x6 | 8 | 6 | 6 | 6 | 6 |
| D_labirinto_61x61 | 4 | 1805 | 692 | 1010 | 956 |
| D_labirinto_61x61 | 8 | 1805 | 692 | 1010 | 956 |
| E_aberto_120x120 | 4 | 13299 | 7835 | 10261 | 10027 |
| E_aberto_120x120 | 8 | 13209 | 110 (custo 136,55 vs. 134,21, ✘) | 1578 | 699 |
| F_terrenos_40x40 | 4 | 837 | 304 | 438 | 402 |
| F_terrenos_40x40 | 8 | 840 | 306 | 430 | 399 |
| G_obstaculo_U_60x60 | 4 | 3443 | 1683 | 2289 | 2175 |
| G_obstaculo_U_60x60 | 8 | 3419 | 1132 | 1491 | 1235 |
| H_aleatorio_80x80 | 4 | 4535 | 4535 | 4535 | 4535 |
| H_aleatorio_80x80 | 8 | 4530 | 4522 | 4527 | 4525 |
| I_sem_caminho_100x100 | 4 | 8976 | 8976 | 8976 | 8976 |
| I_sem_caminho_100x100 | 8 | 8976 | 8976 | 8976 | 8976 |

## Weighted A* (excesso de custo / variação de nós face a w = 1)

| Cenário | Mov. | w=1,0 | w=1,2 | w=1,5 | w=2,0 | w=3,0 | w=5,0 |
|---|---|---|---|---|---|---|---|
| A_labirinto_7x10 | 4 | 0,0% / 0% | 0,0% / 0% | 0,0% / 0% | 0,0% / +37% | 0,0% / +41% | 58,8% / +4% |
| A_labirinto_7x10 | 8 | 0,0% / 0% | 0,0% / 0% | 0,0% / 0% | 0,0% / +4% | 0,0% / +41% | 58,8% / +4% |
| B_terrenos_5x9 | 4 | 0,0% / 0% | 0,0% / −3% | 0,0% / −3% | 0,0% / −3% | 0,0% / −3% | 0,0% / −17% |
| B_terrenos_5x9 | 8 | 0,0% / 0% | 0,0% / −4% | 0,0% / −11% | 0,0% / −11% | 0,0% / −25% | 0,0% / −25% |
| D_labirinto_61x61 | 4 | 0,0% / 0% | 0,0% / −31% | 0,0% / −34% | 13,2% / −52% | 15,8% / −68% | 15,8% / −68% |
| D_labirinto_61x61 | 8 | 0,0% / 0% | 0,0% / −15% | 0,0% / −40% | 0,0% / −72% | 0,0% / −76% | 10,5% / −77% |
| E_aberto_120x120 | 4 | 0,0% / 0% | 1,1% / −97% | 1,1% / −98% | 1,1% / −98% | 1,1% / −98% | 1,1% / −98% |
| E_aberto_120x120 | 8 | 0,0% / 0% | 0,9% / −84% | 0,9% / −85% | 1,7% / −85% | 1,7% / −85% | 1,7% / −85% |
| F_terrenos_40x40 | 4 | 0,0% / 0% | 0,0% / +6% | 0,0% / +14% | 0,0% / +32% | 1,4% / +69% | 190,1% / +41% |
| F_terrenos_40x40 | 8 | 0,0% / 0% | 0,0% / −18% | 0,0% / −26% | 2,4% / −19% | 32,0% / −13% | 45,8% / +52% |
| G_obstaculo_U_60x60 | 4 | 0,0% / 0% | 0,0% / −30% | 0,0% / −32% | 0,0% / −35% | 0,0% / −39% | 0,0% / −43% |
| G_obstaculo_U_60x60 | 8 | 0,0% / 0% | 0,0% / −19% | 0,0% / −25% | 0,0% / −30% | 0,0% / +23% | 1,9% / +83% |
| H_aleatorio_80x80 | 4 | 0,0% / 0% | 0,0% / 0% | 0,0% / 0% | 0,0% / 0% | 0,0% / −2% | 7,3% / −88% |
| H_aleatorio_80x80 | 8 | 0,0% / 0% | 0,0% / 0% | 0,0% / 0% | 0,0% / 0% | 0,0% / −5% | 3,0% / −27% |

## Escalabilidade (mapa aberto n×n, 5% obstáculos, 4 direções)

| n | Configuração | Custo | Nós expandidos | Memória (nós em g) | Tempo (ms) |
|---|---|---|---|---|---|
| 25 | Dijkstra | 38,00 | 570 | 574 | 0,72 |
| 25 | A* Manhattan | 38,00 | 336 | 404 | 0,51 |
| 50 | Dijkstra | 76,00 | 2304 | 2314 | 3,41 |
| 50 | A* Manhattan | 76,00 | 1379 | 1516 | 2,11 |
| 100 | Dijkstra | 154,00 | 9226 | 9245 | 12,50 |
| 100 | A* Manhattan | 154,00 | 5236 | 5519 | 7,86 |
| 150 | Dijkstra | 232,00 | 20791 | 20821 | 29,97 |
| 150 | A* Manhattan | 232,00 | 12105 | 12543 | 19,52 |
| 200 | Dijkstra | 308,00 | 36999 | 37041 | 54,56 |
| 200 | A* Manhattan | 308,00 | 21373 | 21974 | 35,86 |
| 300 | Dijkstra | 464,00 | 83343 | 83405 | 135,31 |
| 300 | A* Manhattan | 464,00 | 47188 | 48116 | 83,80 |

## Terrenos: caminho com menos passos vs. caminho de menor custo

| Mov. | Menos passos: passos / custo | Ótimo: passos / custo |
|---|---|---|
| 4 | 39 / 206,00 | 71 / 71,00 |
| 8 | 37 / 194,97 | 67 / 68,66 |
