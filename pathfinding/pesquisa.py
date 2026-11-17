"""Dijkstra, A* e Weighted A* numa única função de pesquisa.

Prioridade de cada nó na fronteira:
    Dijkstra       f(n) = g(n)
    A*             f(n) = g(n) + h(n)
    Weighted A*    f(n) = g(n) + w·h(n),  w ≥ 1

O teste de objetivo é feito quando o nó é RETIRADO da fronteira (não quando é gerado),
condição necessária para a otimalidade de Dijkstra e de A* com heurística admissível.
"""

from __future__ import annotations

import heapq
import itertools
import math
import time
from dataclasses import dataclass, field

from . import heuristicas
from .grelha import Celula, Grelha

DESEMPATES = ("fifo", "h")

# Tolerância na comparação de custos g. Somas com √2 feitas por ordens diferentes diferem
# em ~1e-16 (ex.: 1 + √2 + 1 vs. 1 + 1 + √2); sem tolerância, esse ruído seria tratado como
# "caminho melhor" e provocaria reaberturas espúrias. As diferenças reais entre custos
# (inteiros e múltiplos de √2) são muitas ordens de grandeza maiores.
EPS = 1e-9


@dataclass
class Resultado:
    caminho: list[Celula] | None      # None se não existir caminho
    custo: float                      # math.inf se não existir caminho
    expandidos: int                   # nós retirados da fronteira e expandidos (inclui reexpansões)
    gerados: int                      # inserções na fronteira
    reaberturas: int                  # nós fechados reabertos (só Weighted A* com reabrir=True)
    memoria: int                      # nós distintos guardados em g (aprox. da memória usada)
    tempo: float                      # segundos (perf_counter)
    fechados: set[Celula] = field(default_factory=set, repr=False)

    @property
    def encontrou(self) -> bool:
        return self.caminho is not None

    @property
    def passos(self) -> int:
        return len(self.caminho) - 1 if self.caminho else 0


def pesquisar(grelha: Grelha, movimento: int = 4, heuristica: str | None = None,
              w: float = 1.0, reabrir: bool | None = None, desempate: str = "fifo") -> Resultado:
    """Pesquisa de custo mínimo de `grelha.inicio` até `grelha.objetivo`.

    movimento   4 ou 8 direções.
    heuristica  None (Dijkstra) ou 'manhattan' | 'euclidiana' | 'octile' (A*).
    w           peso da heurística (Weighted A*); w = 1 é o A* normal.
    reabrir     permitir reabrir nós fechados quando se encontra um g menor.
                Por omissão, só quando w > 1 (com w·h a heurística deixa de ser consistente).
    desempate   'fifo': f igual → ordem de inserção (contador);
                'h':    f igual → menor h primeiro e só depois a ordem de inserção.
    """
    if movimento not in (4, 8):
        raise ValueError("movimento tem de ser 4 ou 8")
    if w < 1:
        raise ValueError("w tem de ser ≥ 1")
    if desempate not in DESEMPATES:
        raise ValueError(f"desempate tem de ser um de {DESEMPATES}")
    if heuristica is None and w != 1:
        raise ValueError("w só faz sentido com uma heurística")
    if reabrir is None:
        reabrir = w > 1

    t0 = time.perf_counter()
    inicio, objetivo = grelha.inicio, grelha.objetivo
    if heuristica is None:
        h = None
    else:
        h = heuristicas.construir(heuristica, objetivo, grelha.custo_min)
    usar_h_desempate = desempate == "h" and h is not None

    contador = itertools.count()
    g: dict[Celula, float] = {inicio: 0.0}
    pai: dict[Celula, Celula | None] = {inicio: None}
    fechados: set[Celula] = set()

    h0 = h(inicio) if h else 0.0
    # Entrada: (f, desempate_h, contador, g, nó). O contador garante ordem total e reprodutível.
    fronteira = [(w * h0, h0 if usar_h_desempate else 0.0, next(contador), 0.0, inicio)]
    expandidos = reaberturas = 0
    gerados = 1
    encontrado = False

    while fronteira:
        _, _, _, g_no, no = heapq.heappop(fronteira)
        # Entradas obsoletas: o nó já foi fechado, ou entretanto encontrou-se um g menor.
        if no in fechados or g_no > g[no]:
            continue
        fechados.add(no)
        expandidos += 1
        if no == objetivo:
            encontrado = True
            break
        for viz, custo_mov in grelha.vizinhos(no, movimento):
            novo_g = g_no + custo_mov
            if novo_g < g.get(viz, math.inf) - EPS:
                if viz in fechados:
                    if not reabrir:
                        continue
                    fechados.discard(viz)
                    reaberturas += 1
                g[viz] = novo_g
                pai[viz] = no
                hv = h(viz) if h else 0.0
                heapq.heappush(fronteira, (novo_g + w * hv, hv if usar_h_desempate else 0.0,
                                           next(contador), novo_g, viz))
                gerados += 1

    caminho = None
    if encontrado:
        caminho = []
        no: Celula | None = objetivo
        while no is not None:
            caminho.append(no)
            no = pai[no]
        caminho.reverse()
    tempo = time.perf_counter() - t0

    return Resultado(
        caminho=caminho,
        custo=g[objetivo] if encontrado else math.inf,
        expandidos=expandidos,
        gerados=gerados,
        reaberturas=reaberturas,
        memoria=len(g),
        tempo=tempo,
        fechados=fechados,
    )


def dijkstra(grelha: Grelha, movimento: int = 4, **kw) -> Resultado:
    return pesquisar(grelha, movimento, heuristica=None, **kw)


def astar(grelha: Grelha, movimento: int = 4, heuristica: str = "manhattan", **kw) -> Resultado:
    return pesquisar(grelha, movimento, heuristica=heuristica, **kw)


def weighted_astar(grelha: Grelha, movimento: int = 4, heuristica: str = "manhattan",
                   w: float = 1.5, **kw) -> Resultado:
    return pesquisar(grelha, movimento, heuristica=heuristica, w=w, **kw)
