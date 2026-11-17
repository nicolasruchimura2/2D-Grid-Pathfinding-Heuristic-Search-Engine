"""Gera os seis cenários criados pelo grupo e guarda-os em cenarios/.

Todos os cenários aleatórios usam random.Random(SEMENTE + desvio), com SEMENTE = 42,
pelo que voltar a correr este script produz exatamente os mesmos ficheiros.

    python gerar_cenarios.py
"""

from __future__ import annotations

import random
from pathlib import Path

from pathfinding import Grelha, dijkstra, mapa_para_texto

SEMENTE = 42
PASTA = Path(__file__).parent / "cenarios"


# --------------------------------------------------------------------- geradores
def labirinto(rng: random.Random, n_celulas: int = 30, abertura: float = 0.10) -> Grelha:
    """Labirinto (2·n+1)² por backtracking recursivo (iterativo), com `abertura` das
    paredes interiores removidas para criar ciclos (vários caminhos possíveis)."""
    lado = 2 * n_celulas + 1
    custos: list[list[int | None]] = [[None] * lado for _ in range(lado)]
    visitado = [[False] * n_celulas for _ in range(n_celulas)]
    pilha = [(0, 0)]
    visitado[0][0] = True
    custos[1][1] = 1
    while pilha:
        l, c = pilha[-1]
        opcoes = [(l + dl, c + dc) for dl, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                  if 0 <= l + dl < n_celulas and 0 <= c + dc < n_celulas
                  and not visitado[l + dl][c + dc]]
        if not opcoes:
            pilha.pop()
            continue
        nl, nc = rng.choice(opcoes)
        visitado[nl][nc] = True
        custos[2 * nl + 1][2 * nc + 1] = 1
        custos[l + nl + 1][c + nc + 1] = 1  # parede entre as duas células
        pilha.append((nl, nc))
    # Paredes interiores que separam duas células (posições com uma coordenada par).
    paredes = [(l, c) for l in range(1, lado - 1) for c in range(1, lado - 1)
               if custos[l][c] is None and (l % 2) != (c % 2)]
    for l, c in rng.sample(paredes, int(abertura * len(paredes))):
        custos[l][c] = 1
    return Grelha(custos, (1, 1), (lado - 2, lado - 2), f"D_labirinto_{lado}x{lado}")


def aberto(rng: random.Random, n: int = 120, densidade: float = 0.05, nome: str | None = None) -> Grelha:
    """Espaço aberto n×n, custo uniforme 1, com `densidade` de obstáculos dispersos."""
    inicio = (n // 8, n // 10)
    objetivo = (n - 1 - n // 8, n - 1 - n // 10)
    custos = [[None if rng.random() < densidade else 1 for _ in range(n)] for _ in range(n)]
    custos[inicio[0]][inicio[1]] = custos[objetivo[0]][objetivo[1]] = 1
    return Grelha(custos, inicio, objetivo, nome or f"E_aberto_{n}x{n}")


def terrenos(rng: random.Random, n: int = 40) -> Grelha:
    """Terrenos 1–9. Entre S e G há uma faixa de pântano (custo 7–9); uma estrada de
    custo 1 contorna-a. O caminho com menos passos atravessa o pântano e é mais caro
    do que o desvio pela estrada."""
    meio = n // 2
    inicio, objetivo = (meio, 1), (meio, n - 2)
    custos: list[list[int | None]] = [[rng.randint(2, 4) for _ in range(n)] for _ in range(n)]
    for l in range(n):
        for c in range(n // 4, 3 * n // 4):          # faixa de pântano
            custos[l][c] = rng.randint(7, 9)
    for l in range(n):                               # alguns rochedos no pântano
        for c in range(n // 4, 3 * n // 4):
            if rng.random() < 0.06:
                custos[l][c] = None
    estrada = set()
    for l in range(3, meio + 1):                     # sobe junto a S
        estrada.add((l, 3))
    for c in range(1, 4):
        estrada.add((meio, c))
    for c in range(3, n - 3):                        # atravessa por cima
        estrada.add((3, c))
    for l in range(3, meio + 1):                     # desce junto a G
        estrada.add((l, n - 4))
    for c in range(n - 4, n - 1):
        estrada.add((meio, c))
    for l, c in estrada:
        custos[l][c] = 1
    return Grelha(custos, inicio, objetivo, f"F_terrenos_{n}x{n}")


def obstaculo_u(n: int = 60) -> Grelha:
    """Obstáculo côncavo em U virado para S, no caminho em linha reta até G.
    A heurística puxa a pesquisa para dentro do U (armadilha clássica do A*)."""
    meio = n // 2
    inicio, objetivo = (meio, 8), (meio, n - 9)
    custos: list[list[int | None]] = [[1] * n for _ in range(n)]
    topo, fundo, esq, dir_ = meio - 16, meio + 16, meio - 8, meio + 8
    for l in range(topo, fundo + 1):
        custos[l][dir_] = None                       # fundo do U (do lado de G)
    for c in range(esq, dir_ + 1):
        custos[topo][c] = None                       # braço de cima
        custos[fundo][c] = None                      # braço de baixo
    return Grelha(custos, inicio, objetivo, f"G_obstaculo_U_{n}x{n}")


def aleatorio(rng: random.Random, n: int = 80, densidade: float = 0.28) -> Grelha:
    """Obstáculos aleatórios densos e custos aleatórios 1–9 em todas as células livres."""
    custos = [[None if rng.random() < densidade else rng.randint(1, 9) for _ in range(n)]
              for _ in range(n)]
    custos[0][0] = custos[n - 1][n - 1] = 1
    return Grelha(custos, (0, 0), (n - 1, n - 1), f"H_aleatorio_{n}x{n}")


def sem_caminho(rng: random.Random, n: int = 100, densidade: float = 0.10) -> Grelha:
    """Mapa grande em que G está fechado num anel de obstáculos: não há caminho.
    Serve para medir o custo de provar que não existe solução."""
    inicio = (n // 10, n // 10)
    objetivo = (3 * n // 4, 4 * n // 5)
    custos: list[list[int | None]] = [[None if rng.random() < densidade else 1 for _ in range(n)]
                                      for _ in range(n)]
    gl, gc = objetivo
    for l in range(gl - 3, gl + 4):
        for c in range(gc - 3, gc + 4):
            anel = max(abs(l - gl), abs(c - gc)) == 3
            custos[l][c] = None if anel else 1
    custos[inicio[0]][inicio[1]] = 1
    return Grelha(custos, inicio, objetivo, f"I_sem_caminho_{n}x{n}")


# ------------------------------------------------------------------------ main
def com_caminho(fabrica, desvio: int) -> tuple[Grelha, int]:
    """Repete com a semente seguinte até o mapa ter caminho (em 4 direções)."""
    for k in range(100):
        grelha = fabrica(random.Random(SEMENTE + desvio + k))
        if dijkstra(grelha, 4).encontrou:
            return grelha, SEMENTE + desvio + k
    raise RuntimeError("não foi possível gerar um mapa com caminho")


def gerar() -> list[tuple[Grelha, str]]:
    cenarios = []
    g, s = com_caminho(labirinto, 0)
    cenarios.append((g, f"semente {s}"))
    g, s = com_caminho(aberto, 100)
    cenarios.append((g, f"semente {s}"))
    g, s = com_caminho(terrenos, 200)
    cenarios.append((g, f"semente {s}"))
    cenarios.append((obstaculo_u(), "determinístico"))
    g, s = com_caminho(aleatorio, 400)
    cenarios.append((g, f"semente {s}"))
    g = sem_caminho(random.Random(SEMENTE + 500))
    assert not dijkstra(g, 8).encontrou
    cenarios.append((g, f"semente {SEMENTE + 500}"))
    return cenarios


def main() -> None:
    PASTA.mkdir(exist_ok=True)
    for grelha, origem in gerar():
        destino = PASTA / f"{grelha.nome}.txt"
        destino.write_text(mapa_para_texto(grelha), encoding="utf-8")
        print(f"{destino.name:28s} {grelha.linhas}x{grelha.colunas}  ({origem})")


if __name__ == "__main__":
    main()
