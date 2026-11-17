"""Testes do planeador.  Correr com:  python -m unittest -v"""

from __future__ import annotations

import math
import unittest
from pathlib import Path

from pathfinding import ErroMapa, analisar_mapa, astar, dijkstra, ler_mapa, pesquisar
from pathfinding.grelha import SQRT2

CENARIOS = Path(__file__).resolve().parent.parent / "cenarios"
ADMISSIVEIS = {4: ("manhattan", "euclidiana", "octile"), 8: ("euclidiana", "octile")}
H_REFERENCIA = {4: "manhattan", 8: "octile"}


class TestLeitura(unittest.TestCase):
    def test_formato_compacto_e_separado_sao_equivalentes(self):
        a = analisar_mapa("S.3\n#9G\n")
        b = analisar_mapa("S . 3\n# 9 G\n")
        self.assertEqual(a.custos, b.custos)
        self.assertEqual((a.inicio, a.objetivo), ((0, 0), (1, 2)))
        self.assertEqual(a.custos, ((1, 1, 3), (None, 9, 1)))

    def test_comentarios_e_linhas_vazias(self):
        g = analisar_mapa("; comentário\n\nSG\n")
        self.assertEqual((g.linhas, g.colunas), (1, 2))

    def test_erros(self):
        for texto in ("S.\n.\nG", "S.x\n..G", "..\n.G", "S.\n.S\nGG", "S0G"):
            with self.subTest(texto=texto), self.assertRaises(ErroMapa):
                analisar_mapa(texto)


class TestMovimento(unittest.TestCase):
    def test_custo_de_entrada_no_destino(self):
        r = dijkstra(analisar_mapa("S5G"), 4)
        self.assertEqual(r.custo, 6)          # entra no 5 e depois no G (custo 1)
        self.assertEqual(r.caminho, [(0, 0), (0, 1), (0, 2)])

    def test_diagonal_custa_raiz_de_2(self):
        r = dijkstra(analisar_mapa("S.\n.G"), 8)
        self.assertAlmostEqual(r.custo, SQRT2)
        self.assertEqual(r.passos, 1)

    def test_diagonal_pesa_o_custo_do_destino(self):
        g = analisar_mapa("S.\n.7\n.G")
        self.assertIn(((1, 1), 7 * SQRT2), list(g.vizinhos((0, 0), 8)))
        # Via (1,1): 7·√2 + 1 ≈ 10,9; pela coluna livre: 1 + 1·√2 ≈ 2,41.
        self.assertAlmostEqual(dijkstra(g, 8).custo, 1 + SQRT2)

    def test_nao_corta_esquinas(self):
        # Um obstáculo num dos ortogonais impede a diagonal.
        g = analisar_mapa("S#\n.G")
        r = dijkstra(g, 8)
        self.assertEqual(r.caminho, [(0, 0), (1, 0), (1, 1)])
        self.assertEqual(r.custo, 2)
        self.assertNotIn(((1, 1), SQRT2), list(g.vizinhos((0, 0), 8)))

    def test_diagonal_entre_dois_obstaculos_proibida(self):
        r = dijkstra(analisar_mapa("S#\n#G"), 8)
        self.assertFalse(r.encontrou)
        self.assertEqual(r.custo, math.inf)


class TestPesquisa(unittest.TestCase):
    def test_sem_caminho_termina(self):
        g = analisar_mapa("S.#..\n..#.G\n..#..")
        for m in (4, 8):
            for r in (dijkstra(g, m), astar(g, m, H_REFERENCIA[m])):
                self.assertFalse(r.encontrou)
                self.assertEqual(r.expandidos, 6)   # toda a região de S, cada nó uma vez

    def test_inicio_igual_a_objetivo_nao_e_permitido_no_formato(self):
        with self.assertRaises(ErroMapa):
            analisar_mapa("S")

    def test_prefere_caminho_mais_barato_ao_mais_curto(self):
        g = analisar_mapa("S9G\n...")
        for m in (4, 8):
            self.assertEqual(dijkstra(g, m).caminho[1], (1, 0) if m == 4 else (1, 1))

    def test_parametros_invalidos(self):
        g = analisar_mapa("SG")
        with self.assertRaises(ValueError):
            pesquisar(g, 6)
        with self.assertRaises(ValueError):
            pesquisar(g, 4, "manhattan", w=0.5)
        with self.assertRaises(ValueError):
            pesquisar(g, 4, "inexistente")
        with self.assertRaises(ValueError):
            pesquisar(g, 4, None, w=2)

    def test_resultados_reprodutiveis(self):
        g = ler_mapa(CENARIOS / "D_labirinto_61x61.txt")
        a, b = astar(g, 8, "octile"), astar(g, 8, "octile")
        self.assertEqual((a.caminho, a.expandidos), (b.caminho, b.expandidos))


class TestCenarios(unittest.TestCase):
    """Propriedades verificadas em todos os cenários da pasta cenarios/."""

    @classmethod
    def setUpClass(cls):
        cls.grelhas = [ler_mapa(p) for p in sorted(CENARIOS.glob("*.txt"))]
        if not cls.grelhas:
            raise unittest.SkipTest("sem cenários; correr gerar_cenarios.py")

    def verificar_caminho(self, g, r, m):
        self.assertEqual(r.caminho[0], g.inicio)
        self.assertEqual(r.caminho[-1], g.objetivo)
        self.assertAlmostEqual(g.custo_caminho(r.caminho, m), r.custo, places=9)

    def test_astar_admissivel_e_otimo(self):
        for g in self.grelhas:
            for m in (4, 8):
                d = dijkstra(g, m)
                for h in ADMISSIVEIS[m]:
                    for desempate in ("fifo", "h"):
                        with self.subTest(cenario=g.nome, mov=m, h=h, desempate=desempate):
                            a = astar(g, m, h, desempate=desempate)
                            self.assertEqual(a.encontrou, d.encontrou)
                            if d.encontrou:
                                self.assertAlmostEqual(a.custo, d.custo, places=9)
                                self.verificar_caminho(g, a, m)
                                self.assertLessEqual(a.expandidos, d.expandidos)

    def test_weighted_respeita_limite(self):
        for g in self.grelhas:
            for m in (4, 8):
                otimo = dijkstra(g, m)
                if not otimo.encontrou:
                    continue
                for w in (1.2, 1.5, 2, 3, 5):
                    for reabrir in (True, False):
                        with self.subTest(cenario=g.nome, mov=m, w=w, reabrir=reabrir):
                            r = pesquisar(g, m, H_REFERENCIA[m], w=w, reabrir=reabrir)
                            self.verificar_caminho(g, r, m)
                            self.assertLessEqual(r.custo, w * otimo.custo + 1e-9)
                            self.assertGreaterEqual(r.custo, otimo.custo - 1e-9)
                            if not reabrir:
                                self.assertEqual(r.reaberturas, 0)

    def test_heuristica_consistente_nunca_reabre(self):
        # Com h consistente (w = 1) um nó fechado já tem o g ótimo: reabrir não pode acontecer.
        for g in self.grelhas:
            for m in (4, 8):
                for h in ADMISSIVEIS[m]:
                    with self.subTest(cenario=g.nome, mov=m, h=h):
                        self.assertEqual(pesquisar(g, m, h, reabrir=True).reaberturas, 0)

    def test_caminho_dijkstra_valido(self):
        for g in self.grelhas:
            for m in (4, 8):
                r = dijkstra(g, m)
                if r.encontrou:
                    with self.subTest(cenario=g.nome, mov=m):
                        self.verificar_caminho(g, r, m)


class TestAnexoA(unittest.TestCase):
    """Validação com os resultados de referência do enunciado (Anexo A)."""

    ESPERADO = {
        "A_labirinto_7x10": (17.0, 17.0),
        "B_terrenos_5x9": (20.0, 18.83),
        "C_sem_caminho_4x6": (math.inf, math.inf),
    }

    def test_custos_de_referencia(self):
        em_falta = []
        for nome, (c4, c8) in self.ESPERADO.items():
            caminho = CENARIOS / f"{nome}.txt"
            if not caminho.exists():
                em_falta.append(caminho.name)
                continue
            g = ler_mapa(caminho)
            for m, esperado in ((4, c4), (8, c8)):
                with self.subTest(cenario=nome, mov=m):
                    for r in (dijkstra(g, m), astar(g, m, H_REFERENCIA[m])):
                        if math.isinf(esperado):
                            self.assertFalse(r.encontrou)
                        else:
                            self.assertAlmostEqual(r.custo, esperado, places=2)
        if em_falta:
            self.skipTest(f"faltam {', '.join(em_falta)} (copiar os mapas do Anexo A do enunciado)")


if __name__ == "__main__":
    unittest.main()
