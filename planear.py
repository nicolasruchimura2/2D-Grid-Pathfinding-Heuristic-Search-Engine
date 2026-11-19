"""Planeia um caminho num mapa e mostra o resultado no terminal.

Exemplos:
    python planear.py cenarios/F_terrenos_40x40.txt
    python planear.py cenarios/D_labirinto_61x61.txt --alg astar --heur octile --mov 8
    python planear.py cenarios/E_aberto_120x120.txt --alg astar --w 2 --sem-mapa
"""

from __future__ import annotations

import argparse

from pathfinding import HEURISTICAS, ler_mapa, pesquisar


def desenhar(grelha, caminho) -> str:
    no_caminho = set(caminho or [])
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
            elif (l, c) in no_caminho:
                simbolos.append("*")
            else:
                simbolos.append("." if custo == 1 else str(custo))
        linhas.append("".join(simbolos))
    return "\n".join(linhas)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mapa", help="ficheiro de cenário (.txt)")
    ap.add_argument("--alg", choices=("dijkstra", "astar"), default="dijkstra")
    ap.add_argument("--heur", choices=sorted(HEURISTICAS), default=None,
                    help="heurística do A* (omissão: manhattan em 4 dir., octile em 8 dir.)")
    ap.add_argument("--mov", type=int, choices=(4, 8), default=4, help="modelo de movimento")
    ap.add_argument("--w", type=float, default=1.0, help="peso da heurística (Weighted A*)")
    ap.add_argument("--sem-mapa", action="store_true", help="não desenhar o mapa")
    args = ap.parse_args()

    grelha = ler_mapa(args.mapa)
    heuristica = None
    if args.alg == "astar":
        heuristica = args.heur or ("manhattan" if args.mov == 4 else "octile")
    elif args.heur or args.w != 1:
        ap.error("--heur e --w só se aplicam com --alg astar")

    r = pesquisar(grelha, args.mov, heuristica, w=args.w)
    nome = "Dijkstra" if heuristica is None else f"A* ({heuristica}, w = {args.w:g})"
    print(f"{grelha.nome}: {grelha.linhas}x{grelha.colunas}, S = {grelha.inicio}, G = {grelha.objetivo}")
    print(f"{nome}, {args.mov} direções")
    if r.encontrou:
        print(f"  custo:       {r.custo:.2f}")
        print(f"  passos:      {r.passos}")
    else:
        print("  não existe caminho entre S e G")
    print(f"  expandidos:  {r.expandidos}")
    if r.reaberturas:
        print(f"  reaberturas: {r.reaberturas}")
    print(f"  tempo:       {r.tempo * 1000:.2f} ms")
    if not args.sem_mapa:
        print()
        print(desenhar(grelha, r.caminho))


if __name__ == "__main__":
    main()
