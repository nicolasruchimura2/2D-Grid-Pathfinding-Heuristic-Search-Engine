"""Heurísticas de distância até ao objetivo.

Todas recebem dx, dy (diferenças absolutas de coordenadas) e são multiplicadas pelo
custo mínimo de uma célula (1 nos nossos mapas), o que mantém a admissibilidade:
nenhum movimento custa menos do que a distância que a heurística assume percorrer.

| heurística  | 4 direções                      | 8 direções                         |
|-------------|---------------------------------|------------------------------------|
| manhattan   | admissível e consistente        | NÃO admissível (sobrestima)        |
| euclidiana  | admissível e consistente        | admissível e consistente           |
| octile      | admissível, dominada pela Manh. | admissível, consistente, a melhor  |
"""

from __future__ import annotations

import math
from typing import Callable

from .grelha import SQRT2, Celula

FuncaoH = Callable[[Celula], float]


def manhattan(dx: int, dy: int) -> float:
    return float(dx + dy)


def euclidiana(dx: int, dy: int) -> float:
    return math.hypot(dx, dy)


def octile(dx: int, dy: int) -> float:
    return (dx + dy) + (SQRT2 - 2.0) * min(dx, dy)


HEURISTICAS: dict[str, Callable[[int, int], float]] = {
    "manhattan": manhattan,
    "euclidiana": euclidiana,
    "octile": octile,
}


def construir(nome: str, objetivo: Celula, custo_min: float = 1.0) -> FuncaoH:
    """Devolve h(n) para o objetivo dado."""
    try:
        base = HEURISTICAS[nome]
    except KeyError:
        raise ValueError(f"heurística desconhecida {nome!r}; opções: {sorted(HEURISTICAS)}") from None
    gl, gc = objetivo

    def h(cel: Celula) -> float:
        return custo_min * base(abs(cel[0] - gl), abs(cel[1] - gc))

    return h
