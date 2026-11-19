"""Corre todas as experiências do relatório e guarda resultados e figuras.

    python experiencias.py            # N = 10 repetições por medição de tempo
    python experiencias.py --rep 3    # mais rápido

Saídas:
    resultados/comparacao.csv      cenário × algoritmo × heurística × movimento
    resultados/weighted.csv        Weighted A* para w ∈ {1; 1,2; 1,5; 2; 3; 5}
    resultados/escalabilidade.csv  mapas abertos n×n de tamanho crescente
    resultados/tabelas.md          tabelas prontas a colar no relatório
    figuras/*.png                  gráficos e mapas com caminhos
"""

from __future__ import annotations

import argparse
import csv
import gc
import heapq
import math
import random
import statistics
from pathlib import Path

from pathfinding import Grelha, ler_mapa, pesquisar
from gerar_cenarios import SEMENTE, aberto

RAIZ = Path(__file__).parent
CENARIOS = RAIZ / "cenarios"
RESULTADOS = RAIZ / "resultados"
FIGURAS = RAIZ / "figuras"

HEURISTICAS = ("manhattan", "euclidiana", "octile")
H_REF = {4: "manhattan", 8: "octile"}       # heurística de referência por modelo de movimento
PESOS = (1.0, 1.2, 1.5, 2.0, 3.0, 5.0)
TAMANHOS = (25, 50, 100, 150, 200, 300)

ANEXO_A = {  # custos esperados (4 dir., 8 dir.) do enunciado
    "A_labirinto_7x10": (17.0, 17.0),
    "B_terrenos_5x9": (20.0, 18.83),
    "C_sem_caminho_4x6": (math.inf, math.inf),
}

# Paleta categórica de referência (ordem fixa) e tinta de texto.
COR = {"dijkstra": "#2a78d6", "manhattan": "#eb6834", "euclidiana": "#1baf7a", "octile": "#eda100"}
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
TINTA, TINTA2, GRELHA_COR, FUNDO = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


# ---------------------------------------------------------------- utilitários
def medir(grelha: Grelha, rep: int, **kw):
    """Corre a pesquisa `rep` vezes; devolve o último resultado e (média, desvio) do tempo em ms.
    Custo, caminho e nós expandidos são determinísticos e confirmados em todas as repetições."""
    tempos, ref = [], None
    gc.collect()
    gc.disable()
    try:
        for _ in range(rep):
            r = pesquisar(grelha, **kw)
            tempos.append(r.tempo * 1000)
            if ref is None:
                ref = r
            elif (r.custo, r.expandidos) != (ref.custo, ref.expandidos):
                raise AssertionError("resultado não determinístico")
    finally:
        gc.enable()
    desvio = statistics.stdev(tempos) if len(tempos) > 1 else 0.0
    return ref, statistics.mean(tempos), desvio


def menos_passos(grelha: Grelha, movimento: int):
    """Entre os caminhos com o menor número de passos, o de menor custo.
    Serve para mostrar que no cenário de terrenos o caminho mais curto não é o mais barato."""
    dist = {grelha.inicio: (0, 0.0)}
    pai = {grelha.inicio: None}
    fila = [(0, 0.0, grelha.inicio)]
    while fila:
        p, c, no = heapq.heappop(fila)
        if (p, c) > dist[no]:
            continue
        if no == grelha.objetivo:
            caminho = []
            while no is not None:
                caminho.append(no)
                no = pai[no]
            return caminho[::-1], p, c
        for viz, custo in grelha.vizinhos(no, movimento):
            novo = (p + 1, c + custo)
            if novo < dist.get(viz, (math.inf, math.inf)):
                dist[viz] = novo
                pai[viz] = no
                heapq.heappush(fila, (*novo, viz))
    return None, math.inf, math.inf


def num(x: float, casas: int = 2) -> str:
    """Formato português (vírgula decimal)."""
    if isinstance(x, float) and math.isinf(x):
        return "sem caminho"
    return f"{x:.{casas}f}".replace(".", ",")


ROTULOS = {"labirinto": "labirinto", "aberto": "aberto", "terrenos": "terrenos",
           "obstaculo_U": "obstáculo em U", "aleatorio": "aleatório", "sem_caminho": "sem caminho"}


def nome_curto(nome: str) -> str:
    letra, resto = nome.split("_", 1)
    tipo = resto.rsplit("_", 1)[0]
    return f"{letra}: {ROTULOS.get(tipo, tipo.replace('_', ' '))}"


def escrever_csv(caminho: Path, linhas: list[dict]) -> None:
    with caminho.open("w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(linhas[0]))
        escritor.writeheader()
        escritor.writerows(linhas)


# ---------------------------------------------------------------- experiências
def comparar(grelhas: list[Grelha], rep: int) -> list[dict]:
    linhas = []
    for g in grelhas:
        for m in (4, 8):
            otimo = None
            for h in (None, *HEURISTICAS):
                r, t, dt = medir(g, rep, movimento=m, heuristica=h)
                if h is None:
                    otimo = r.custo
                linhas.append({
                    "cenario": g.nome, "dimensao": f"{g.linhas}x{g.colunas}", "movimento": m,
                    "algoritmo": "Dijkstra" if h is None else "A*", "heuristica": h or "-",
                    "custo": r.custo, "otimo": math.isclose(r.custo, otimo) or r.custo == otimo,
                    "passos": r.passos, "expandidos": r.expandidos, "gerados": r.gerados,
                    "memoria": r.memoria, "tempo_ms": round(t, 3), "tempo_desvio_ms": round(dt, 3),
                })
    return linhas


def weighted(grelhas: list[Grelha], rep: int) -> list[dict]:
    linhas = []
    for g in grelhas:
        for m in (4, 8):
            otimo = pesquisar(g, m).custo
            if math.isinf(otimo):
                continue
            base = None
            for w in PESOS:
                r, t, _ = medir(g, rep, movimento=m, heuristica=H_REF[m], w=w)
                base = base or r.expandidos
                linhas.append({
                    "cenario": g.nome, "movimento": m, "heuristica": H_REF[m], "w": w,
                    "custo": r.custo, "custo_otimo": otimo,
                    "excesso": r.custo / otimo - 1, "limite": w - 1,
                    "expandidos": r.expandidos, "reaberturas": r.reaberturas,
                    "variacao_nos": r.expandidos / base - 1, "tempo_ms": round(t, 3),
                })
    return linhas


def escalabilidade(rep: int) -> list[dict]:
    linhas = []
    for n in TAMANHOS:
        g = aberto(random.Random(SEMENTE + 100), n=n, nome=f"aberto_{n}x{n}")
        for rotulo, kw in (("Dijkstra", {}), ("A* Manhattan", {"heuristica": "manhattan"})):
            r, t, _ = medir(g, rep, movimento=4, **kw)
            linhas.append({"n": n, "celulas": n * n, "configuracao": rotulo, "custo": r.custo,
                           "expandidos": r.expandidos, "memoria": r.memoria, "tempo_ms": round(t, 3)})
    return linhas


# ---------------------------------------------------------------- figuras
def estilo(plt) -> None:
    plt.rcParams.update({
        "figure.facecolor": FUNDO, "axes.facecolor": FUNDO, "savefig.facecolor": FUNDO,
        "axes.edgecolor": GRELHA_COR, "axes.labelcolor": TINTA2, "text.color": TINTA,
        "xtick.color": TINTA2, "ytick.color": TINTA2, "axes.grid": True, "grid.color": GRELHA_COR,
        "grid.linewidth": 0.8, "axes.axisbelow": True, "axes.spines.top": False,
        "axes.spines.right": False, "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold",
        "legend.frameon": False, "lines.linewidth": 2,
    })


def fig_heuristicas(plt, comp: list[dict]) -> None:
    fig, eixos = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    series = ("dijkstra", *HEURISTICAS)
    rotulos = {"dijkstra": "Dijkstra", "manhattan": "A* Manhattan",
               "euclidiana": "A* Euclidiana", "octile": "A* Octile"}
    for ax, m in zip(eixos, (4, 8)):
        dados = [l for l in comp if l["movimento"] == m and l["custo"] != math.inf]
        cenarios = list(dict.fromkeys(l["cenario"] for l in dados))
        largura = 0.2
        for i, s in enumerate(series):
            xs, ys = [], []
            for j, c in enumerate(cenarios):
                base = next(l for l in dados if l["cenario"] == c and l["algoritmo"] == "Dijkstra")
                linha = base if s == "dijkstra" else next(
                    l for l in dados if l["cenario"] == c and l["heuristica"] == s)
                xs.append(j + (i - 1.5) * largura)
                ys.append(100 * linha["expandidos"] / base["expandidos"])
                if not linha["otimo"]:
                    excesso = 100 * (linha["custo"] / base["custo"] - 1)
                    ax.annotate(f"custo\n+{num(excesso, 1)}%", (xs[-1], ys[-1]), xytext=(0, 3),
                                textcoords="offset points", ha="center", va="bottom",
                                fontsize=7, color=TINTA)
            barras = ax.bar(xs, ys, largura * 0.9, color=COR[s], label=rotulos[s])
            for b, c in zip(barras, cenarios):
                linha = next((l for l in dados if l["cenario"] == c and l["heuristica"] == s), None)
                if linha and not linha["otimo"]:
                    b.set_hatch("////")
                    b.set_edgecolor(FUNDO)
        ax.set_xticks(range(len(cenarios)), [nome_curto(c) for c in cenarios], rotation=25, ha="right")
        ax.set_title(f"{m} direções")
        ax.set_ylim(0, 118)
        ax.grid(axis="x", visible=False)
    eixos[0].set_ylabel("nós expandidos (% do Dijkstra)")
    fig.tight_layout(rect=(0, 0.03, 1, 0.92))
    pegas, rotulos_ = eixos[0].get_legend_handles_labels()
    fig.legend(pegas, rotulos_, loc="upper center", ncol=4, bbox_to_anchor=(0.5, 1.0))
    fig.text(0.99, 0.005, "Barras tracejadas: caminho subótimo (heurística não admissível).",
             ha="right", fontsize=7.5, color=TINTA2)
    fig.savefig(FIGURAS / "heuristicas_nos_expandidos.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig_weighted(plt, wa: list[dict]) -> None:
    fig, eixos = plt.subplots(2, 2, figsize=(11, 7), sharex=True)
    cenarios = list(dict.fromkeys(l["cenario"] for l in wa))
    for col, m in enumerate((4, 8)):
        ax_n, ax_e = eixos[0][col], eixos[1][col]
        for i, c in enumerate(cenarios):
            pts = [l for l in wa if l["cenario"] == c and l["movimento"] == m]
            ws = [p["w"] for p in pts]
            ax_n.plot(ws, [100 * p["expandidos"] / pts[0]["expandidos"] for p in pts],
                      marker="o", ms=4, color=SERIES[i], label=nome_curto(c))
            ax_e.plot(ws, [100 * p["excesso"] for p in pts], marker="o", ms=4, color=SERIES[i])
        maximo = max(100 * l["excesso"] for l in wa)
        ax_e.plot(PESOS, [100 * (w - 1) for w in PESOS], ls="--", color=TINTA2, lw=1.5,
                  label="limite teórico (w − 1)")
        ax_e.set_ylim(-1, max(5.0, maximo * 1.6))
        ax_e.text(1.25, max(5.0, maximo * 1.6) * 0.93, "limite teórico w − 1 (tracejado) ↑",
                  fontsize=7.5, color=TINTA2)
        ax_n.set_title(f"{m} direções (heurística {H_REF[m]})")
        topo = max(100 * l["expandidos"] / next(b for b in wa if b["cenario"] == l["cenario"]
                   and b["movimento"] == l["movimento"] and b["w"] == 1.0)["expandidos"] for l in wa)
        ax_n.set_ylim(0, topo * 1.08)
        ax_n.axhline(100, color=TINTA2, lw=1, ls=":")
        ax_e.set_xlabel("peso w")
        ax_e.set_xticks(PESOS, [num(w, 1).replace(",0", "") for w in PESOS])
    eixos[0][0].set_ylabel("nós expandidos (% de w = 1)")
    eixos[1][0].set_ylabel("excesso de custo (%)")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    pegas, rotulos_ = eixos[0][0].get_legend_handles_labels()
    fig.legend(pegas, rotulos_, loc="upper center", ncol=len(cenarios), bbox_to_anchor=(0.5, 1.0))
    fig.savefig(FIGURAS / "weighted_astar.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig_weighted_compacto(plt, wa: list[dict], movimento: int = 4) -> None:
    """Versão de uma linha para o mini-relatório: só os cenários grandes, um modelo de movimento."""
    pts_todos = [l for l in wa if l["movimento"] == movimento
                 and not l["cenario"].startswith(tuple("ABC"))]
    cenarios = list(dict.fromkeys(l["cenario"] for l in pts_todos))
    fig, (ax_n, ax_e) = plt.subplots(1, 2, figsize=(10, 3.1))
    for i, c in enumerate(cenarios):
        pts = [l for l in pts_todos if l["cenario"] == c]
        ws = [p["w"] for p in pts]
        ax_n.plot(ws, [100 * p["expandidos"] / pts[0]["expandidos"] for p in pts], marker="o", ms=4,
                  color=SERIES[i], label=nome_curto(c))
        ax_e.plot(ws, [100 * p["excesso"] for p in pts], marker="o", ms=4, color=SERIES[i])
    ax_e.plot(PESOS, [100 * (w - 1) for w in PESOS], ls="--", color=TINTA2, lw=1.5)
    maximo = max(100 * p["excesso"] for p in pts_todos)
    ax_e.set_ylim(-2, maximo * 1.15)
    ax_e.text(1.45, maximo * 1.02, "limite w − 1", fontsize=8, color=TINTA2)
    ax_n.axhline(100, color=TINTA2, lw=1, ls=":")
    ax_n.set_ylabel("nós expandidos (% de w = 1)")
    ax_e.set_ylabel("excesso de custo (%)")
    for ax in (ax_n, ax_e):
        ax.set_xlabel(f"peso w ({movimento} direções, {H_REF[movimento]})")
        ax.set_xticks(PESOS, [num(w, 1).replace(",0", "") for w in PESOS])
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    pegas, rotulos_ = ax_n.get_legend_handles_labels()
    fig.legend(pegas, rotulos_, loc="upper center", ncol=len(cenarios), bbox_to_anchor=(0.5, 1.0))
    fig.savefig(FIGURAS / "weighted_astar_compacto.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig_escalabilidade(plt, esc: list[dict]) -> None:
    fig, eixos = plt.subplots(1, 2, figsize=(11, 4))
    configs = list(dict.fromkeys(l["configuracao"] for l in esc))
    for i, cfg in enumerate(configs):
        pts = [l for l in esc if l["configuracao"] == cfg]
        xs = [p["celulas"] / 1000 for p in pts]
        eixos[0].plot(xs, [p["expandidos"] / 1000 for p in pts], marker="o", ms=4,
                      color=SERIES[i], label=cfg)
        eixos[1].plot(xs, [p["tempo_ms"] for p in pts], marker="o", ms=4, color=SERIES[i])
    eixos[0].set_ylabel("nós expandidos (milhares)")
    eixos[1].set_ylabel("tempo médio (ms)")
    for ax in eixos:
        ax.set_xlabel("células da grelha (milhares)")
    eixos[0].set_title("Nós expandidos")
    eixos[1].set_title("Tempo de execução")
    eixos[0].legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(FIGURAS / "escalabilidade.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig_caminhos(plt, g: Grelha, movimento: int = 4) -> None:
    """Dijkstra vs. A* lado a lado: obstáculos, custos, nós expandidos e caminho."""
    import numpy as np
    from matplotlib.colors import ListedColormap

    custos = np.array([[np.nan if c is None else c for c in fila] for fila in g.custos], dtype=float)
    resultados = [("Dijkstra", pesquisar(g, movimento)),
                  (f"A* {H_REF[movimento]}", pesquisar(g, movimento, H_REF[movimento]))]
    extra = None
    if g.nome.startswith("F_"):
        extra = menos_passos(g, movimento)[0]
    lado = 5.2 if g.colunas >= g.linhas else 5.2 * g.colunas / g.linhas
    fig, eixos = plt.subplots(1, 2, figsize=(2 * lado + 0.6, 5.6))
    cinzas = ListedColormap([str(1 - 0.06 * k) for k in range(1, 10)])
    for ax, (titulo, r) in zip(eixos, resultados):
        ax.imshow(custos, cmap=cinzas, vmin=0.5, vmax=9.5, interpolation="nearest")
        obst = np.where(np.isnan(custos), 1.0, np.nan)
        ax.imshow(obst, cmap=ListedColormap(["#3b3a37"]), interpolation="nearest")
        explor = np.full(custos.shape, np.nan)
        for l, c in r.fechados:
            explor[l, c] = 1
        ax.imshow(explor, cmap=ListedColormap(["#2a78d6"]), alpha=0.28, interpolation="nearest")
        if extra:
            ax.plot([c for _, c in extra], [l for l, _ in extra], color="#e34948", lw=1.6,
                    ls="--", label="menos passos")
        if r.caminho:
            ax.plot([c for _, c in r.caminho], [l for l, _ in r.caminho], color="#eb6834", lw=2,
                    label="ótimo")
        for (l, c), letra in ((g.inicio, "S"), (g.objetivo, "G")):
            ax.plot(c, l, "o", ms=9, color=TINTA, mec=FUNDO, mew=1.5)
            ax.text(c, l, letra, color=FUNDO, ha="center", va="center", fontsize=6, weight="bold")
        custo = num(r.custo) if r.encontrou else "sem caminho"
        ax.set_title(f"{titulo}: custo {custo} · {r.expandidos} nós expandidos", fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        for s in ax.spines.values():
            s.set_visible(False)
        if extra:
            ax.legend(loc="lower right", fontsize=7, frameon=True)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.text(0.5, 0.01, f"{g.nome}, {movimento} direções. Azul: nós expandidos · cinzento: custo "
             "da célula (mais escuro = mais caro) · preto: obstáculo", ha="center", fontsize=8,
             color=TINTA2)
    destino = FIGURAS / "caminhos"
    destino.mkdir(exist_ok=True)
    fig.savefig(destino / f"{g.nome}_{movimento}dir.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- tabelas
def tabelas(grelhas, comp, wa, esc) -> str:
    def linha_de(c, m, alg, h="-"):
        return next(l for l in comp if l["cenario"] == c and l["movimento"] == m
                    and l["algoritmo"] == alg and l["heuristica"] == h)

    out = ["# Tabelas geradas por experiencias.py", ""]

    out += ["## Validação (Anexo A)", "",
            "| Cenário | Custo 4 dir. (esperado → obtido) | Custo 8 dir. (esperado → obtido) "
            "| Nós 4 dir. Dijkstra / A* Manhattan |", "|---|---|---|---|"]
    nomes = {g.nome for g in grelhas}
    for nome, esperados in ANEXO_A.items():
        if nome not in nomes:
            out.append(f"| {nome} | ficheiro em falta | ficheiro em falta | – |")
            continue
        cel = []
        for m, e in zip((4, 8), esperados):
            obtido = linha_de(nome, m, "Dijkstra")["custo"]
            ok = (math.isinf(e) and math.isinf(obtido)) or abs(obtido - e) < 0.005
            cel.append(f"{num(e)} → {num(obtido)} {'✔' if ok else '✘'}")
        nos = f"{linha_de(nome, 4, 'Dijkstra')['expandidos']} / {linha_de(nome, 4, 'A*', 'manhattan')['expandidos']}"
        out.append(f"| {nome} | {cel[0]} | {cel[1]} | {nos} |")

    out += ["", "## Dijkstra vs. A* (4 direções, Manhattan)", "",
            "| Cenário | Dijkstra: custo / nós / tempo (ms) | A*: custo / nós / tempo (ms) | Ganho em nós | Ganho em tempo |",
            "|---|---|---|---|---|"]
    for g in grelhas:
        d, a = linha_de(g.nome, 4, "Dijkstra"), linha_de(g.nome, 4, "A*", "manhattan")
        gn = 1 - a["expandidos"] / d["expandidos"]
        gt = 1 - a["tempo_ms"] / d["tempo_ms"]
        out.append(f"| {g.nome} | {num(d['custo'])} / {d['expandidos']} / {num(d['tempo_ms'])} "
                   f"| {num(a['custo'])} / {a['expandidos']} / {num(a['tempo_ms'])} "
                   f"| {num(100 * gn, 1)}% | {num(100 * gt, 1)}% |")

    out += ["", "## Heurísticas e modelos de movimento (nós expandidos; custo se subótimo)", "",
            "| Cenário | Mov. | Dijkstra | Manhattan | Euclidiana | Octile |", "|---|---|---|---|---|---|"]
    for g in grelhas:
        for m in (4, 8):
            d = linha_de(g.nome, m, "Dijkstra")
            cels = [f"{d['expandidos']}"]
            for h in HEURISTICAS:
                l = linha_de(g.nome, m, "A*", h)
                s = f"{l['expandidos']}"
                if not l["otimo"]:
                    s += f" (custo {num(l['custo'])} vs. {num(d['custo'])}, ✘)"
                cels.append(s)
            out.append(f"| {g.nome} | {m} | " + " | ".join(cels) + " |")

    def var(x: float) -> str:
        pct = round(100 * x)
        return ("+" if pct > 0 else "−" if pct < 0 else "") + f"{abs(pct)}%"

    out += ["", "## Weighted A* (excesso de custo / variação de nós face a w = 1)", "",
            "| Cenário | Mov. | " + " | ".join(f"w={num(w, 1)}" for w in PESOS) + " |",
            "|---|---|" + "---|" * len(PESOS)]
    for c in dict.fromkeys(l["cenario"] for l in wa):
        for m in (4, 8):
            pts = [l for l in wa if l["cenario"] == c and l["movimento"] == m]
            out.append(f"| {c} | {m} | " + " | ".join(
                f"{num(100 * p['excesso'], 1)}% / {var(p['variacao_nos'])}" for p in pts) + " |")

    out += ["", "## Escalabilidade (mapa aberto n×n, 5% obstáculos, 4 direções)", "",
            "| n | Configuração | Custo | Nós expandidos | Memória (nós em g) | Tempo (ms) |",
            "|---|---|---|---|---|---|"]
    for l in esc:
        out.append(f"| {l['n']} | {l['configuracao']} | {num(l['custo'])} | {l['expandidos']} "
                   f"| {l['memoria']} | {num(l['tempo_ms'])} |")

    terr = [g for g in grelhas if g.nome.startswith("F_")]
    if terr:
        g = terr[0]
        out += ["", "## Terrenos: caminho com menos passos vs. caminho de menor custo", "",
                "| Mov. | Menos passos: passos / custo | Ótimo: passos / custo |", "|---|---|---|"]
        for m in (4, 8):
            _, p, c = menos_passos(g, m)
            d = linha_de(g.nome, m, "Dijkstra")
            out.append(f"| {m} | {p} / {num(c)} | {d['passos']} / {num(d['custo'])} |")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rep", type=int, default=10, help="repetições por medição de tempo (omissão: 10)")
    ap.add_argument("--sem-figuras", action="store_true")
    args = ap.parse_args()

    RESULTADOS.mkdir(exist_ok=True)
    FIGURAS.mkdir(exist_ok=True)
    grelhas = [ler_mapa(p) for p in sorted(CENARIOS.glob("*.txt"))]
    if not grelhas:
        raise SystemExit("Sem cenários em cenarios/. Correr primeiro: python gerar_cenarios.py")
    em_falta = [n for n in ANEXO_A if not (CENARIOS / f"{n}.txt").exists()]
    if em_falta:
        print("AVISO: faltam os cenários do Anexo A:", ", ".join(em_falta))

    print(f"{len(grelhas)} cenários, {args.rep} repetições por medição")
    print("· comparação de algoritmos e heurísticas")
    comp = comparar(grelhas, args.rep)
    print("· Weighted A*")
    wa = weighted(grelhas, args.rep)
    print("· escalabilidade")
    esc = escalabilidade(max(3, args.rep // 2))

    escrever_csv(RESULTADOS / "comparacao.csv", comp)
    escrever_csv(RESULTADOS / "weighted.csv", wa)
    escrever_csv(RESULTADOS / "escalabilidade.csv", esc)
    md = tabelas(grelhas, comp, wa, esc)
    (RESULTADOS / "tabelas.md").write_text(md, encoding="utf-8")

    if not args.sem_figuras:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        estilo(plt)
        print("· figuras")
        fig_heuristicas(plt, comp)
        fig_weighted(plt, wa)
        fig_weighted_compacto(plt, wa)
        fig_escalabilidade(plt, esc)
        for g in grelhas:
            fig_caminhos(plt, g, 4)
            fig_caminhos(plt, g, 8)
    print(md)


if __name__ == "__main__":
    main()
