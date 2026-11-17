"""Modelo do mapa: grelha 2D com custos de entrada por célula e obstáculos.

Formato dos ficheiros de cenário (texto UTF-8):
    S   início (custo de entrada 1)
    G   objetivo (custo de entrada 1)
    #   obstáculo (intransponível)
    .   célula livre com custo 1
    1-9 célula livre com o custo indicado

As células podem estar coladas ("S.3#G") ou separadas por espaços ("S . 3 # G").
Linhas vazias e linhas começadas por ';' são ignoradas (comentários).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Iterator

Celula = tuple[int, int]

SQRT2 = math.sqrt(2.0)

# Ordem fixa dos movimentos: garante resultados reprodutíveis.
MOV_ORTOGONAIS: tuple[Celula, ...] = ((-1, 0), (0, 1), (1, 0), (0, -1))  # N, E, S, O
MOV_DIAGONAIS: tuple[Celula, ...] = ((-1, 1), (1, 1), (1, -1), (-1, -1))  # NE, SE, SO, NO


class ErroMapa(ValueError):
    """Mapa mal formado (símbolo inválido, grelha não retangular, S/G em falta…)."""


class Grelha:
    """Grelha imutável. `custos[l][c]` é o custo de entrada (1-9) ou None se for obstáculo."""

    __slots__ = ("custos", "inicio", "objetivo", "nome", "linhas", "colunas", "custo_min")

    def __init__(self, custos, inicio: Celula, objetivo: Celula, nome: str = "") -> None:
        self.custos: tuple[tuple[int | None, ...], ...] = tuple(tuple(l) for l in custos)
        self.linhas = len(self.custos)
        self.colunas = len(self.custos[0]) if self.linhas else 0
        if self.linhas == 0 or self.colunas == 0:
            raise ErroMapa("a grelha está vazia")
        if any(len(l) != self.colunas for l in self.custos):
            raise ErroMapa("a grelha não é retangular")
        for nome_cel, cel in (("início", inicio), ("objetivo", objetivo)):
            if not self.livre(cel):
                raise ErroMapa(f"o {nome_cel} {cel} está fora da grelha ou num obstáculo")
        self.inicio = inicio
        self.objetivo = objetivo
        self.nome = nome
        livres = [c for linha in self.custos for c in linha if c is not None]
        if any(not (1 <= c <= 9) for c in livres):
            raise ErroMapa("os custos das células têm de estar entre 1 e 9")
        # Custo mínimo de entrada: escala as heurísticas sem perder a admissibilidade.
        self.custo_min = min(livres)

    # ------------------------------------------------------------------ consultas
    def dentro(self, cel: Celula) -> bool:
        l, c = cel
        return 0 <= l < self.linhas and 0 <= c < self.colunas

    def livre(self, cel: Celula) -> bool:
        l, c = cel
        return 0 <= l < self.linhas and 0 <= c < self.colunas and self.custos[l][c] is not None

    def custo(self, cel: Celula) -> int:
        valor = self.custos[cel[0]][cel[1]]
        if valor is None:
            raise ValueError(f"{cel} é um obstáculo")
        return valor

    def vizinhos(self, cel: Celula, movimento: int) -> Iterator[tuple[Celula, float]]:
        """Sucessores de `cel` e o custo de cada movimento.

        Ortogonal: custo(destino). Diagonal: custo(destino)·√2, permitida só se as
        duas células ortogonais adjacentes estiverem livres (não se cortam esquinas).
        """
        l, c = cel
        custos = self.custos
        nl, nc = self.linhas, self.colunas
        for dl, dc in MOV_ORTOGONAIS:
            vl, vc = l + dl, c + dc
            if 0 <= vl < nl and 0 <= vc < nc:
                custo = custos[vl][vc]
                if custo is not None:
                    yield (vl, vc), float(custo)
        if movimento == 8:
            for dl, dc in MOV_DIAGONAIS:
                vl, vc = l + dl, c + dc
                if (0 <= vl < nl and 0 <= vc < nc
                        and custos[vl][vc] is not None
                        and custos[l][vc] is not None      # vizinho horizontal
                        and custos[vl][c] is not None):    # vizinho vertical
                    yield (vl, vc), custos[vl][vc] * SQRT2

    def custo_caminho(self, caminho: list[Celula], movimento: int) -> float:
        """Recalcula e valida o custo de um caminho (útil para testes)."""
        total = 0.0
        for a, b in zip(caminho, caminho[1:]):
            for viz, custo in self.vizinhos(a, movimento):
                if viz == b:
                    total += custo
                    break
            else:
                raise ValueError(f"movimento inválido {a} -> {b} em {movimento} direções")
        return total

    def __repr__(self) -> str:
        return f"Grelha({self.nome!r}, {self.linhas}x{self.colunas}, S={self.inicio}, G={self.objetivo})"


# ---------------------------------------------------------------------- leitura
def analisar_mapa(texto: str, nome: str = "") -> Grelha:
    linhas = [l.strip() for l in texto.splitlines()]
    linhas = [l for l in linhas if l and not l.startswith(";")]
    if not linhas:
        raise ErroMapa("mapa vazio")
    separado = any(" " in l or "\t" in l for l in linhas)
    custos: list[list[int | None]] = []
    inicio = objetivo = None
    for i, linha in enumerate(linhas):
        simbolos = linha.split() if separado else list(linha)
        fila: list[int | None] = []
        for j, s in enumerate(simbolos):
            if s == "#":
                fila.append(None)
            elif s == ".":
                fila.append(1)
            elif s in "123456789" and len(s) == 1:
                fila.append(int(s))
            elif s in ("S", "G"):
                if (s == "S" and inicio) or (s == "G" and objetivo):
                    raise ErroMapa(f"'{s}' aparece mais do que uma vez (linha {i + 1})")
                if s == "S":
                    inicio = (i, j)
                else:
                    objetivo = (i, j)
                fila.append(1)
            else:
                raise ErroMapa(f"símbolo inválido {s!r} na linha {i + 1}, coluna {j + 1}")
        custos.append(fila)
    if inicio is None or objetivo is None:
        raise ErroMapa("o mapa tem de ter exatamente um 'S' e um 'G'")
    return Grelha(custos, inicio, objetivo, nome)


def ler_mapa(caminho: str | Path) -> Grelha:
    caminho = Path(caminho)
    return analisar_mapa(caminho.read_text(encoding="utf-8"), nome=caminho.stem)


def mapa_para_texto(grelha: Grelha) -> str:
    """Serializa a grelha no formato compacto (uma linha de símbolos por linha)."""
    linhas = []
    for l, fila in enumerate(grelha.custos):
        simbolos = []
        for c, custo in enumerate(fila):
            if (l, c) == grelha.inicio:
                simbolos.append("S")
            elif (l, c) == grelha.objetivo:
                simbolos.append("G")
            elif custo is None:
                simbolos.append("#")
            elif custo == 1:
                simbolos.append(".")
            else:
                simbolos.append(str(custo))
        linhas.append("".join(simbolos))
    return "\n".join(linhas) + "\n"
