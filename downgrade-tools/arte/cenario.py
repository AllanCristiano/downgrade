"""Cenario da Fase 1 (Aterro 9): tileset, objetos animados, luzes e fundos com parallax."""
from __future__ import annotations

import math
import random

from pixel import BAYER4, Img, alfa, fbm, ruido, texto

T = 32
K = (10, 4, 18)

SOLO = [(12, 6, 16), (22, 12, 26), (34, 21, 38), (50, 33, 52)]
METAL = [(30, 30, 42), (70, 70, 88), (122, 122, 142), (186, 186, 204)]
FERRUGEM = [(50, 22, 14), (96, 44, 22), (140, 72, 34), (176, 104, 52)]
BORRACHA = [(10, 8, 14), (24, 20, 28), (42, 38, 50), (68, 64, 78)]
PLASTICO = [(8, 6, 12), (20, 16, 26), (36, 30, 46), (70, 64, 92)]
CIANO = (0, 240, 255)
ROSA = (255, 42, 109)
AMARELO = (255, 209, 102)
VERDE = (61, 255, 154)
LUZ_NEON = (110, 52, 104)

PINTURAS = {
    "vermelho": [(60, 14, 22), (112, 30, 36), (160, 52, 48), (200, 96, 80)],
    "azul": [(16, 26, 52), (30, 52, 92), (52, 84, 128), (98, 130, 168)],
    "verde": [(14, 40, 40), (26, 74, 70), (44, 110, 98), (96, 160, 140)],
    "amarelo": [(70, 48, 14), (130, 96, 26), (186, 146, 46), (226, 196, 104)],
}


def tom_dither(v: float, x: int, y: int, n: int = 4) -> int:
    """Converte 0..1 em indice de rampa com dithering ordenado (transicoes suaves em pixel art)."""
    v = max(0.0, min(0.999, v)) * n
    i = int(v)
    if (v - i) > (BAYER4[y % 4][x % 4] + 0.5) / 16:
        i += 1
    return min(n - 1, i)


# ======================================================================== TILES SOLIDOS

def chao(seed: int, topo: bool, fundo: bool = False) -> Img:
    r = random.Random(seed)
    t = Img(T, T)
    n = fbm(T, T, seed, (16, 8, 4))
    for y in range(T):
        for x in range(T):
            v = n[y][x] * 1.05 - 0.12 - (0.25 if fundo else 0) - y / T * 0.12
            if (y + int(n[y][x] * 6)) % 9 == 0:  # camadas de lixo compactado
                v -= 0.18
            t.set(x, y, SOLO[tom_dither(v, x, y, 4)])
    # entulho enterrado
    for _ in range(2 if not fundo else 1):
        x, y = r.randrange(2, 28), r.randrange(8 if topo else 2, 28)
        tipo = r.choice(["lata", "pedra", "osso_de_metal", "garrafa"])
        if tipo == "lata":
            t.capsula(x, y, x + 4, y + 1, 1.6, 1.6, FERRUGEM)
        elif tipo == "placa":
            t.rect(x, y, 5, 3, (20, 70, 40))
            t.set(x + 1, y + 1, AMARELO)
            t.set(x + 3, y + 1, (200, 170, 80))
        elif tipo == "pedra":
            t.elipse(x, y, 2.4, 1.8, [SOLO[1], SOLO[2], SOLO[3], (70, 54, 72)])
        elif tipo == "osso_de_metal":
            t.linha(x, y, x + 5, y + r.choice([-1, 1]), METAL[1])
        else:
            t.capsula(x, y, x + 3, y - 1, 1.2, 1.0, [alfa((0, 120, 140), 200)] * 3 + [alfa(CIANO, 230)], borda=False)
    if r.random() < 0.5:
        t.set(r.randrange(T), r.randrange(6, T), r.choice([(0, 110, 130), (130, 30, 80)]))
    if topo:
        h = 1
        for x in range(T):
            h = max(0, min(2, h + r.choice([-1, 0, 0, 0, 1])))
            for y in range(h):
                t.set(x, y, None)
            t.set(x, h, LUZ_NEON)
            t.set(x, h + 1, SOLO[3])
            t.set(x, h + 2, SOLO[2])
        # detritos por cima
        for _ in range(2):
            x = r.randrange(3, 27)
            obj = r.choice(["fio", "lata", "tabua"])
            if obj == "fio":
                for i in range(8):
                    t.set(x + i, 2 + round(math.sin(i * 0.9)), METAL[0])
                t.set(x + 8, 2, (200, 90, 40))
            elif obj == "lata":
                t.capsula(x, 2.5, x + 3, 2.5, 1.5, 1.5, FERRUGEM)
            else:
                t.rect(x, 2, 6, 2, (70, 46, 30))
                t.rect(x, 2, 6, 1, (110, 76, 48))
    return t


def fardo(cor: str, seed: int) -> Img:
    """Fardo de carros prensados (plataformas)."""
    r = random.Random(seed)
    tinta = PINTURAS[cor]
    t = Img(T, T)
    n = fbm(T, T, seed, (8, 4, 2))
    ferr = ruido(T, T, 6, seed + 9)
    for y in range(T):
        for x in range(T):
            v = 0.25 + n[y][x] * 0.65 - y / T * 0.2
            if ferr[y][x] > 0.75:
                t.set(x, y, FERRUGEM[tom_dither(v, x, y)])
            else:
                t.set(x, y, tinta[tom_dither(v, x, y)])
    # dobras da lataria amassada
    for _ in range(9):
        x0, y0 = r.randrange(T), r.randrange(4, T - 4)
        comp = r.randrange(4, 10)
        inc = r.choice([-1, -0.5, 0.5, 1])
        for i in range(comp):
            x, y = x0 + i, round(y0 + i * inc * 0.4)
            t.set(x % T, y, tinta[0])
            t.set(x % T, y - 1, tinta[3] if i % 2 else tinta[2])
    # pecas reconheciveis
    x, y = r.randrange(4, 24), r.randrange(10, 24)
    pecas = r.choice(["farol", "maçaneta", "vidro", "placa"])
    if pecas == "farol":
        t.elipse(x, y, 2.2, 1.6, [(120, 100, 40), (200, 170, 70), (255, 230, 140), (255, 250, 220)])
    elif pecas == "maçaneta":
        t.rect(x, y, 5, 1, METAL[2])
        t.rect(x, y + 1, 5, 1, METAL[0])
    elif pecas == "vidro":
        for i in range(4):
            t.set(x + i, y + (i % 2), alfa(CIANO, 160))
    else:
        t.rect(x, y, 7, 3, (210, 210, 220))
        t.rect(x + 1, y + 1, 5, 1, (40, 40, 60))
    # cintas de aco
    for yy in (8, 22):
        for x in range(T):
            t.set(x, yy, METAL[2])
            t.set(x, yy + 1, METAL[0])
        t.rect(14, yy - 1, 3, 4, METAL[1])
        t.set(15, yy, METAL[3])
    # aresta de cubo: topo claro, base escura, lados
    for x in range(T):
        t.set(x, 0, tinta[3])
        t.set(x, 1, LUZ_NEON if x % 5 else tinta[3])
        t.set(x, T - 1, K)
        t.set(x, T - 2, tinta[0])
    for y in range(T):
        t.set(0, y, tinta[0])
        t.set(T - 1, y, K)
    return t


def pilha_pneus(topo: bool) -> Img:
    t = Img(T, T)
    for i, cy in enumerate((5, 15, 25)):
        cx = 16 + (1 if i % 2 else -1)
        t.elipse(cx, cy, 15, 5.2, BORRACHA)
        for x in range(cx - 13, cx + 14, 3):  # sulcos
            t.set(x, cy - 2, BORRACHA[0])
            t.set(x + 1, cy + 2, BORRACHA[0])
        t.rect(cx - 15, cy, 30, 1, BORRACHA[0])
    if topo:
        for y in range(0, 4):
            for x in range(T):
                t.set(x, y, None)
        t.elipse(16, 6, 14, 4, BORRACHA)
        t.elipse(16, 6, 7, 1.8, [(6, 2, 10)] * 4, borda=False)
        for x in range(4, 28):
            t.set(x, 2, LUZ_NEON)
    return t


def caixa_perigo() -> Img:
    t = Img(T, T)
    t.capsula(4, 4, 28, 4, 0.1, 0.1, METAL)
    t.rect(0, 0, T, T, METAL[0])
    t.rect(2, 2, T - 4, T - 4, METAL[1])
    t.rect(2, 2, T - 4, 2, METAL[2])
    t.rect(2, 2, 2, T - 4, METAL[2])
    for y in range(12, 20):
        for x in range(2, T - 2):
            t.set(x, y, AMARELO if ((x + y) // 3) % 2 == 0 else (24, 20, 20))
    for x, y in ((4, 5), (27, 5), (4, 27), (27, 27)):
        t.set(x, y, K)
        t.set(x, y - 1, METAL[3])
    for x in range(T):
        t.set(x, 0, LUZ_NEON)
    return t


# ======================================================================== DECORACAO (tiles)

def pneu_solto() -> Img:
    t = Img(T, T)
    t.elipse(16, 23, 8.5, 8.5, BORRACHA)
    t.elipse(16, 23, 4, 4, [(6, 2, 10)] * 4, borda=False)
    t.anel(16, 23, 4, 5, METAL[0])
    for a in range(0, 360, 40):
        t.set(16 + math.cos(math.radians(a)) * 7.5, 23 + math.sin(math.radians(a)) * 7.5, BORRACHA[3])
    t.contorno(K)
    return t


def sacos() -> Img:
    t = Img(T, T)
    t.elipse(10, 25, 8, 6.5, PLASTICO)
    t.elipse(22, 26, 7, 5.5, PLASTICO)
    t.elipse(15, 18, 5.5, 5, PLASTICO)
    t.capsula(15, 13, 16, 11, 1.2, 0.8, PLASTICO)
    for x, y in ((8, 21), (19, 23), (13, 15)):
        t.set(x, y, (120, 110, 150))
    t.contorno(K)
    return t


def geladeira() -> tuple[Img, Img]:
    g = Img(T, T * 2)
    BRANCO_SUJO = [(70, 66, 74), (128, 122, 126), (176, 170, 168), (214, 210, 204)]
    g.rect(6, 10, 21, 54, BRANCO_SUJO[1])
    for y in range(10, 64):
        g.set(6, y, BRANCO_SUJO[0])
        g.set(7, y, BRANCO_SUJO[0])
        g.set(25, y, BRANCO_SUJO[2])
        g.set(26, y, BRANCO_SUJO[3])
    g.rect(6, 10, 21, 2, BRANCO_SUJO[3])
    g.rect(6, 30, 21, 1, BRANCO_SUJO[0])
    g.rect(22, 16, 2, 10, METAL[1])
    g.rect(22, 36, 2, 12, METAL[1])
    n = ruido(T, 64, 5, 41)
    for y in range(10, 64):
        for x in range(6, 27):
            if n[y][x] > 0.72:
                g.set(x, y, FERRUGEM[1 + (n[y][x] > 0.8)])
    g.rect(10, 40, 6, 5, (200, 60, 110))  # adesivo
    g.set(12, 42, (255, 230, 240))
    g.contorno(K)
    return g.recorte(0, 0, T, T), g.recorte(0, T, T, T)


def cerca() -> tuple[Img, Img]:
    c = Img(T, T * 2)
    for y in range(6, 64):
        for x in range(1, 31):
            if (x + y) % 6 == 0 or (x - y) % 6 == 0:
                if not (12 < x < 20 and 20 < y < 34):  # rasgo
                    c.set(x, y, alfa(METAL[2], 200))
    c.capsula(2, 4, 2, 63, 1.4, 1.4, METAL)
    c.capsula(29, 6, 29, 63, 1.4, 1.4, METAL)
    c.linha(2, 6, 29, 8, METAL[1])
    for x in range(12, 21, 2):  # arame farpado
        c.set(x, 20 - (x % 3), METAL[3])
    return c.recorte(0, 0, T, T), c.recorte(0, T, T, T)


def cadaver() -> tuple[Img, Img]:
    """Helena Duarte, onde Marco encontrou a Escama. A nuca ainda brilha."""
    c = Img(T * 2, T)
    ch = 30
    for x in range(14, 58):
        c.set(x, ch + 1, (46, 6, 26))
    c.rect(18, ch, 34, 1, (60, 8, 34))
    JALECO = [(46, 46, 62), (88, 90, 110), (136, 138, 158), (186, 188, 204)]
    CAL = [(20, 18, 30), (36, 34, 52), (58, 56, 78), (84, 82, 106)]
    c.capsula(6, ch - 3, 20, ch - 3, 2.6, 2.8, CAL)
    c.capsula(8, ch - 1, 20, ch - 1, 2.4, 2.6, CAL)
    c.capsula(3, ch - 4, 5, ch - 1, 2.2, 2.2, [(22, 14, 20), (48, 30, 32), (82, 56, 48), (124, 92, 72)])
    c.capsula(19, ch - 3, 40, ch - 4, 4.6, 4.2, JALECO)
    c.capsula(30, ch - 7, 42, ch - 9, 1.8, 1.6, JALECO)  # braco
    c.elipse(43.5, ch - 9.5, 1.7, 1.5, [(60, 30, 40), (120, 70, 60), (170, 110, 86), (210, 150, 120)])
    c.elipse(47, ch - 4, 4, 3.6, [(60, 30, 40), (120, 70, 60), (170, 110, 86), (210, 150, 120)])
    CAB = [(12, 6, 14), (26, 14, 26), (44, 26, 40), (70, 46, 62)]
    c.poligono_sombreado([(44, ch - 8), (52, ch - 9), (59, ch - 5), (61, ch - 1), (54, ch), (49, ch - 1), (45, ch - 2)], CAB, 52, ch - 4, 8, 5)
    c.contorno(K)
    c.brilho(44, ch - 2, 5, CIANO, 170)
    c.set(44, ch - 2, CIANO)
    c.set(45, ch - 2, (180, 255, 255))
    return c.recorte(0, 0, T, T), c.recorte(T, 0, T, T)


def carcaca_carro() -> list[Img]:
    """Sedan sem rodas, 3x2 tiles."""
    c = Img(T * 3, T * 2)
    TINTA = [(14, 34, 40), (24, 64, 70), (40, 100, 100), (90, 150, 140)]
    base = 58
    corpo = [(4, base), (2, base - 12), (8, base - 18), (24, base - 20), (34, base - 34), (62, base - 35),
             (76, base - 22), (90, base - 19), (93, base - 8), (90, base)]
    c.poligono_sombreado(corpo, TINTA, 50, base - 30, 50, 30)
    n = ruido(T * 3, T * 2, 6, 77)
    for x, y in Img.pixels_poligono(corpo):
        if n[y % (T * 2)][x % (T * 3)] > 0.74:
            c.set(x, y, FERRUGEM[0 + (n[y % 64][x % 96] > 0.8)])
    # janelas quebradas com reflexo
    for jan in ([(37, base - 31), (48, base - 31), (48, base - 21), (31, base - 21)],
                [(51, base - 31), (61, base - 31), (71, base - 21), (51, base - 21)]):
        c.poligono(jan, (10, 8, 20))
        xs = [p[0] for p in jan]
        for i in range(4):
            c.set(min(xs) + 3 + i * 2, base - 28 + i * 2, alfa(CIANO, 140))
    c.rect(10, base - 13, 80, 1, TINTA[0])
    c.rect(40, base - 20, 1, 19, TINTA[0])
    for cx in (20, 74):  # caixas de roda vazias
        c.elipse(cx, base, 9, 7, [(6, 2, 10)] * 4, borda=False)
    c.rect(88, base - 16, 4, 3, (255, 140, 66))  # lanterna
    c.rect(4, base - 14, 4, 2, (255, 230, 150))
    c.contorno(K)
    return [c.recorte(i % 3 * T, i // 3 * T, T, T) for i in range(6)]


def entulho() -> Img:
    t = Img(T, T)
    t.capsula(5, 28, 12, 27, 2, 1.8, FERRUGEM)
    t.rect(13, 24, 9, 6, (20, 70, 40))
    t.rect(14, 25, 7, 1, (60, 140, 80))
    t.set(16, 27, AMARELO)
    t.capsula(22, 29, 29, 26, 1.4, 1.2, METAL)
    t.elipse(9, 25, 2.4, 1.8, METAL)
    t.contorno(K)
    return t


NOMES_TILES = [
    "chao_topo_1", "chao_topo_2", "chao_topo_3", "chao_topo_4", "chao_meio_1", "chao_meio_2", "chao_meio_3", "chao_fundo",
    "fardo_vermelho", "fardo_azul", "fardo_verde", "fardo_amarelo", "pneus_topo", "pneus_meio", "caixa", "vazio",
    "pneu", "sacos", "geladeira_cima", "geladeira_baixo", "cerca_cima", "cerca_baixo", "cadaver_1", "cadaver_2",
    "carro_1", "carro_2", "carro_3", "entulho", "vazio2", "vazio3", "vazio4", "vazio5",
    "carro_4", "carro_5", "carro_6", "vazio6", "vazio7", "vazio8", "vazio9", "vazio10",
]


def tileset() -> Img:
    t: dict[str, Img] = {}
    for i in range(4):
        t[f"chao_topo_{i + 1}"] = chao(10 + i, True)
    for i in range(3):
        t[f"chao_meio_{i + 1}"] = chao(20 + i, False)
    t["chao_fundo"] = chao(30, False, fundo=True)
    for i, cor in enumerate(PINTURAS):
        t[f"fardo_{cor}"] = fardo(cor, 40 + i)
    t["pneus_topo"], t["pneus_meio"] = pilha_pneus(True), pilha_pneus(False)
    t["caixa"] = caixa_perigo()
    t["pneu"], t["sacos"], t["entulho"] = pneu_solto(), sacos(), entulho()
    t["geladeira_cima"], t["geladeira_baixo"] = geladeira()
    t["cerca_cima"], t["cerca_baixo"] = cerca()
    t["cadaver_1"], t["cadaver_2"] = cadaver()
    for i, img in enumerate(carcaca_carro()):
        t[f"carro_{i + 1}"] = img
    ts = Img(8 * T, math.ceil(len(NOMES_TILES) / 8) * T)
    for i, nome in enumerate(NOMES_TILES):
        if nome in t:
            ts.colar(t[nome], (i % 8) * T, (i // 8) * T)
    return ts


# ======================================================================== OBJETOS ANIMADOS

def barril_fogo() -> list[Img]:
    q = []
    for f in range(6):
        r = random.Random(100 + f)
        b = Img(32, 48)
        # chamas
        for i in range(26):
            x = 9 + r.random() * 14
            h = 6 + r.random() * 14 * (1 - abs(x - 16) / 10)
            for k in range(int(h)):
                y = 24 - k
                ox = math.sin((k + f * 2 + i) * 0.7) * 1.2
                cor = (255, 240, 180) if k < h * 0.3 else (AMARELO if k < h * 0.6 else (255, 110, 40))
                b.set(x + ox, y, cor)
        for i in range(3):  # brasas
            b.set(10 + r.random() * 12, 4 + r.random() * 10, (255, 160, 60))
        b.capsula(16, 26, 16, 46, 7.5, 7.5, FERRUGEM)
        for yy in (30, 40):
            b.rect(9, yy, 15, 1, FERRUGEM[0])
        b.rect(10, 24, 13, 2, (40, 14, 8))
        b.contorno(K)
        b.brilho(16, 22, 10, (255, 140, 40), 90)
        q.append(b)
    return q


def letreiro_neon() -> list[Img]:
    q = []
    for f in range(4):
        n = Img(96, 44)
        n.rect(3, 4, 90, 26, (14, 8, 22))
        for x in range(3, 93):
            n.set(x, 4, (0, 120, 140))
            n.set(x, 29, (0, 120, 140))
        for y in range(4, 30):
            n.set(3, y, (0, 120, 140))
            n.set(92, y, (0, 120, 140))
        n.capsula(14, 30, 14, 43, 1.3, 1.3, METAL)
        n.capsula(82, 30, 82, 43, 1.3, 1.3, METAL)
        acesas = {0: set(), 1: set(), 2: {3}, 3: {0, 1, 2, 3, 4, 5, 6, 7}}[f]
        cores = {i: (90, 20, 50) for i in acesas}
        brilho = Img(96, 44)
        texto(brilho, 17, 10, "ATERRO 9", alfa(ROSA, 90), 2, {i: alfa((0, 0, 0), 0) for i in acesas})
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)):
            n.colar(brilho, dx, dy)
        texto(n, 17, 10, "ATERRO 9", ROSA, 2, cores)
        texto(n, 32, 23, "PROIBIDO", (0, 160, 180) if f != 3 else (0, 60, 70), 1)
        n.contorno(K)
        q.append(n)
    return q


def tv() -> list[Img]:
    q = []
    for f in range(4):
        r = random.Random(200 + f)
        t = Img(32, 32)
        t.capsula(8, 22, 24, 22, 7, 7, [(26, 24, 34), (50, 48, 62), (80, 78, 96), (120, 118, 140)])
        t.rect(6, 15, 21, 15, (40, 38, 52))
        t.rect(6, 15, 21, 1, (90, 88, 106))
        t.rect(8, 17, 14, 11, (8, 8, 14))
        for y in range(18, 27):
            for x in range(9, 21):
                t.set(x, y, r.choice([(0, 140, 160), (60, 60, 90), (220, 240, 255), (0, 90, 110), (30, 30, 50)]))
        t.rect(23, 18, 2, 2, (200, 40, 80))
        t.rect(23, 22, 2, 1, METAL[2])
        t.linha(13, 15, 9, 7, METAL[2])
        t.linha(17, 15, 22, 8, METAL[2])
        t.contorno(K)
        t.brilho(15, 22, 10, CIANO, 60)
        q.append(t)
    return q


def poste() -> list[Img]:
    q = []
    for f in range(2):
        p = Img(32, 96)
        p.capsula(8, 10, 8, 95, 1.8, 2.2, METAL)
        p.capsula(8, 10, 22, 8, 1.4, 1.4, METAL)
        p.capsula(19, 9, 27, 11, 2.6, 2.2, METAL)
        p.rect(4, 90, 9, 6, METAL[1])
        p.contorno(K)
        luz = (255, 236, 170) if f == 0 else (200, 170, 110)
        p.rect(20, 12, 7, 2, luz)
        p.brilho(23, 13, 6, AMARELO, 200 if f == 0 else 90)
        q.append(p)
    return q


def barril_toxico() -> list[Img]:
    q = []
    for f in range(4):
        b = Img(32, 32)
        b.capsula(16, 14, 16, 31, 7.5, 7.5, [(20, 40, 30), (40, 80, 56), (70, 120, 80), (120, 170, 110)])
        b.rect(9, 18, 15, 1, (20, 40, 30))
        b.rect(9, 26, 15, 1, (20, 40, 30))
        b.elipse(16, 12, 7, 2.2, [(20, 140, 80), (40, 200, 110), VERDE, (200, 255, 220)], borda=False)
        b.rect(13, 20, 6, 4, AMARELO)  # simbolo de perigo
        b.set(15, 21, K)
        b.set(16, 22, K)
        b.contorno(K)
        for i in range(3):
            y = 10 - ((f * 2 + i * 3) % 9)
            b.set(12 + i * 4, y, alfa(VERDE, 200 - (10 - y) * 15))
        b.brilho(16, 11, 9, VERDE, 80)
        q.append(b)
    return q


def saida() -> dict[str, list[Img]]:
    """Porta de correr 48x96: fechada (pisca), abrindo, aberta."""
    def porta(abertura: float, luz, brilho_luz: float) -> Img:
        s = Img(48, 96)
        s.rect(2, 8, 44, 88, METAL[0])
        s.rect(2, 8, 44, 3, METAL[2])
        s.rect(2, 8, 3, 88, METAL[1])
        s.rect(43, 8, 3, 88, (20, 20, 30))
        s.rect(7, 14, 34, 82, (4, 2, 8))
        # interior verde (aparece conforme abre)
        for y in range(14, 96):
            a = 40 + 160 * (y - 14) / 82
            s.rect(7, y, 34, 1, (20, 140, 80, int(a * abertura)))
        h = round(82 * (1 - abertura))
        for y in range(14, 14 + h):
            for x in range(7, 41):
                s.set(x, y, METAL[1] if (y - 14 - (82 - h)) % 8 else METAL[0])
            s.set(7, y, METAL[2])
        if h > 6:
            for y in range(14 + h - 6, 14 + h):
                for x in range(7, 41):
                    s.set(x, y, AMARELO if ((x + y) // 3) % 2 == 0 else (24, 20, 20))
        s.rect(16, 0, 16, 7, K)
        s.rect(18, 2, 12, 3, luz)
        s.contorno(K)
        s.brilho(24, 4, 9, luz, 170 * brilho_luz)
        return s

    return {
        "fechada": [porta(0, ROSA, 1), porta(0, (120, 20, 50), 0.2)],
        "abrindo": [porta(t / 5, VERDE, 1) for t in range(6)],
        "aberta": [porta(1, VERDE, 1), porta(1, VERDE, 0.6)],
    }


def luzes() -> dict[str, Img]:
    radial = Img(128, 128)
    for y in range(128):
        for x in range(128):
            d = math.hypot(x + 0.5 - 64, y + 0.5 - 64) / 64
            if d < 1:
                v = (1 - d) ** 1.8
                v = round(v * 10) / 10
                radial.set(x, y, (255, 255, 255, int(255 * v)))
    cone = Img(96, 160)
    for y in range(160):
        meia = 4 + y * 0.28
        for x in range(96):
            dx = abs(x + 0.5 - 48) / meia
            if dx < 1:
                v = (1 - dx) * (1 - y / 160) ** 1.2
                v = round(v * 8) / 8
                cone.set(x, y, (255, 255, 255, int(200 * v)))
    return {"luz": radial, "cone": cone}


# ======================================================================== FUNDOS (480x272, parallax)
FW, FH = 480, 272


def _gradiente(img: Img, paradas):
    for y in range(FH):
        t = y / FH
        for i in range(len(paradas) - 1):
            if paradas[i][0] <= t <= paradas[i + 1][0]:
                t0, c0 = paradas[i]
                t1, c1 = paradas[i + 1]
                local = (t - t0) / (t1 - t0)
                break
        for x in range(FW):
            img.px[y][x] = c1 if local > (BAYER4[y % 4][x % 4] + 0.5) / 16 else c0


def fundo_ceu() -> Img:
    r = random.Random(1)
    img = Img(FW, FH)
    _gradiente(img, [(0, (6, 2, 16)), (0.3, (12, 4, 30)), (0.55, (26, 10, 48)), (0.75, (50, 16, 66)), (0.9, (86, 24, 86)), (1, (120, 34, 100))])
    for _ in range(70):
        img.set(r.randrange(FW), r.randrange(int(FH * 0.5)), r.choice([(60, 50, 90), (100, 90, 140), (150, 140, 190)]))
    # lua enorme atras do smog
    LUA = [(70, 36, 80), (110, 66, 116), (150, 100, 150), (186, 140, 180)]
    img.brilho(392, 52, 40, (160, 90, 160), 45, passos=True)
    img.elipse(392, 52, 22, 22, LUA, borda=False)
    for cx, cy, rr in ((385, 46, 4), (400, 60, 3), (396, 42, 2), (382, 58, 2.5)):
        img.elipse(cx, cy, rr, rr * 0.9, [LUA[0], LUA[1], LUA[1], LUA[2]], borda=False)
    # faixas de smog na frente da lua, iluminadas por baixo
    for i in range(7):
        cy = r.randrange(40, 170)
        cx = r.randrange(FW)
        w, h = r.randrange(80, 200), r.randrange(4, 9)
        for y in range(cy, cy + h):
            recuo = abs(y - cy - h / 2) * 6
            for x in range(int(cx - w / 2 + recuo), int(cx + w / 2 - recuo)):
                if BAYER4[y % 4][x % 4] < 12:
                    img.set(x % FW, y, (24, 10, 40))
        for x in range(int(cx - w / 2 + 10), int(cx + w / 2 - 10)):
            img.set(x % FW, cy + h, (110, 40, 100))
    return img


def _predio(img: Img, r: random.Random, x0: int, w: int, h: int, cor, borda, janelas: float, cores_jan, base=FH):
    topo = base - h
    for y in range(topo, base):
        for x in range(x0, x0 + w):
            img.set(x % FW, y, cor)
        img.set(x0 % FW, y, borda)
    for x in range(x0, x0 + w):
        img.set(x % FW, topo, borda)
    for y in range(topo + 4, base - 2, 4):
        for x in range(x0 + 2, x0 + w - 2, 3):
            if r.random() < janelas:
                img.set(x % FW, y, r.choice(cores_jan))
    return topo


def fundo_cidade_longe() -> Img:
    r = random.Random(2)
    img = Img(FW, FH)
    x = 0
    while x < FW:
        w = r.randrange(14, 34)
        _predio(img, r, x, w, r.randrange(70, 140), (22, 10, 40), (32, 16, 56), 0.15, [(30, 70, 90), (90, 30, 70)])
        x += w + r.randrange(0, 4)
    # Torre Ofidia + holofotes
    tx, tw = 300, 30
    topo = FH - 250
    for i, (ang, cor) in enumerate(((-28, (0, 200, 230)), (24, (255, 60, 140)))):
        for k in range(160):
            y = topo + 10 - k
            cx = tx + tw / 2 + math.tan(math.radians(ang)) * k
            meia = 1 + k * 0.08
            for xx in range(int(cx - meia), int(cx + meia) + 1):
                img.set(xx % FW, y, alfa(cor, 40))
    for y in range(topo, FH):
        rec = 0 if y > topo + 40 else (4 if y > topo + 16 else 9)
        for xx in range(tx + rec, tx + tw - rec):
            img.set(xx, y, (16, 8, 32))
        img.set(tx + rec, y, (34, 26, 66))
        img.set(tx + tw - rec - 1, y, (0, 140, 170) if y % 3 else (10, 60, 80))
    for y in range(topo + 46, FH, 4):
        img.set(tx + 9, y, (10, 80, 100))
        img.set(tx + 20, y, (10, 80, 100))
    for y in range(topo - 24, topo):
        img.set(tx + tw // 2, y, (34, 26, 66))
    img.set(tx + tw // 2, topo - 25, ROSA)
    ex, ey = tx + tw // 2, topo + 26
    img.brilho(ex, ey, 18, CIANO, 90)
    for dy in range(-9, 10):
        larg = 7 - abs(dy) * 7 // 9
        for dx in range(-larg, larg + 1):
            borda = abs(dx) == larg
            img.set(ex + dx, ey + dy, CIANO if borda else ((0, 160, 190) if dy % 3 == 0 else (0, 90, 120)))
    return img


def fundo_cidade_perto() -> Img:
    r = random.Random(3)
    img = Img(FW, FH)
    cor, borda = (30, 14, 50), (52, 26, 80)
    jan = [(40, 110, 130), (150, 40, 90), (160, 130, 70), (50, 80, 120)]
    predios = []
    x = 6
    while x < FW:
        w = r.randrange(26, 56)
        h = r.randrange(90, 170)
        topo = _predio(img, r, x, w, h, cor, borda, 0.28, jan)
        predios.append((x, w, topo))
        if r.random() < 0.6:  # caixa d'agua / antena
            img.rect((x + 4) % FW, topo - 6, 8, 6, borda)
            img.rect((x + 5) % FW, topo - 6, 6, 1, (70, 40, 100))
        x += w + r.randrange(6, 18)
    # letreiros
    x, w, topo = predios[1]
    img.rect(x + w - 6, topo + 10, 7, 44, (8, 4, 16))
    for i, ch in enumerate("OFIDIA"):
        texto(img, x + w - 5, topo + 13 + i * 7, ch, CIANO, 1)
    img.brilho(x + w - 2, topo + 32, 16, CIANO, 50)
    x, w, topo = predios[3]
    bx, by = x - 4, topo - 26
    img.rect(bx, by, 50, 22, (12, 6, 22))
    img.rect(bx, by, 50, 1, ROSA)
    img.rect(bx, by + 21, 50, 1, ROSA)
    texto(img, bx + 4, by + 4, "ESCAMA", ROSA, 1)
    texto(img, bx + 4, by + 12, "GEN-9", (255, 230, 240), 1)
    for dy in range(-5, 6):  # emblema
        larg = 4 - abs(dy) * 4 // 5
        for dx in range(-larg, larg + 1):
            img.set(bx + 40 + dx, by + 11 + dy, CIANO if abs(dx) == larg else (0, 100, 130))
    img.brilho(bx + 25, by + 11, 28, ROSA, 40)
    img.linha(bx + 10, by + 22, bx + 10, topo, borda)
    img.linha(bx + 40, by + 22, bx + 40, topo, borda)
    x, w, topo = predios[5 % len(predios)]
    img.rect(x + 3, topo + 20, w - 6, 9, (10, 4, 20))
    texto(img, x + 5, topo + 22, "UPGRADE", AMARELO, 1)
    img.brilho(x + w / 2, topo + 24, 18, AMARELO, 40)
    # fios entre predios
    for i in range(len(predios) - 1):
        (x0, w0, t0), (x1, _, t1) = predios[i], predios[i + 1]
        a, b = (x0 + w0, t0 + 14), (x1, t1 + 16)
        for k in range(21):
            t = k / 20
            img.set(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t + math.sin(t * math.pi) * 6, (20, 8, 34))
    return img


def _montes(seed, base, amp, cor, borda, freq=(2, 5, 13)) -> tuple[Img, list[int]]:
    img = Img(FW, FH)
    def h(x):
        p = 2 * math.pi * x / FW
        return round(base + amp * math.sin(freq[0] * p + seed) + amp * 0.55 * math.sin(freq[1] * p + seed * 2)
                     + amp * 0.18 * math.sin(freq[2] * p))
    tops = [h(x) for x in range(FW)]
    for x in range(FW):
        for y in range(tops[x], FH):
            img.px[y][x] = cor
        img.set(x, tops[x], borda)
    return img, tops


def fundo_lixo_longe() -> Img:
    r = random.Random(4)
    cor, borda = (20, 8, 32), (96, 36, 98)
    img, tops = _montes(1.0, 196, 18, cor, borda)
    for _ in range(12):  # silhuetas de sucata no cume
        x0 = r.randrange(FW)
        w, hh, inc = r.randrange(6, 20), r.randrange(4, 12), r.choice([-4, 0, 3])
        by = tops[x0] + 2
        for i in range(w):
            topo_y = by - hh + (i * inc) // max(1, w)
            for y in range(topo_y, by):
                img.set((x0 + i) % FW, y, cor)
            img.set((x0 + i) % FW, topo_y, borda)
    gx = 120  # guindaste
    gy = tops[gx]
    img.linha(gx, gy, gx + 4, gy - 80, cor, 3)
    img.linha(gx + 4, gy - 80, gx + 80, gy - 68, cor, 2)
    img.linha(gx + 4, gy - 81, gx + 80, gy - 69, borda, 1)
    img.linha(gx + 72, gy - 68, gx + 72, gy - 40, (40, 18, 50), 1)
    img.rect(gx + 67, gy - 40, 10, 6, cor)
    img.set(gx + 4, gy - 83, ROSA)
    for _ in range(5):  # fogueiras
        x = r.randrange(FW)
        y = tops[x] + r.randrange(6, 30)
        img.brilho(x, y, 6, (255, 120, 40), 110)
        img.set(x, y, AMARELO)
        img.set(x, y - 1, (255, 240, 200))
    return img


def fundo_lixo_perto() -> Img:
    r = random.Random(5)
    cor, borda = (12, 4, 22), (120, 44, 112)
    img, tops = _montes(2.5, 230, 16, cor, borda, (3, 7, 17))
    for _ in range(10):
        x0 = r.randrange(FW)
        tipo = r.choice(["carro", "geladeira", "pneu", "cano"])
        by = tops[x0] + 3
        if tipo == "carro":
            pts = [(x0, by), (x0 + 2, by - 8), (x0 + 12, by - 10), (x0 + 18, by - 18), (x0 + 34, by - 18), (x0 + 42, by - 9), (x0 + 48, by)]
            img.poligono([((px) % FW, py) for px, py in pts], cor)
            for px, py in zip(pts, pts[1:]):
                img.linha(px[0], px[1], py[0], py[1], borda)
        elif tipo == "geladeira":
            img.rect(x0, by - 22, 10, 22, cor)
            img.rect(x0, by - 22, 10, 1, borda)
            img.rect(x0 + 9, by - 22, 1, 22, borda)
        elif tipo == "pneu":
            img.anel(x0, by - 6, 3, 7, cor)
            img.anel(x0, by - 6, 6.5, 7.2, borda)
        else:
            img.linha(x0, by, x0 + 10, by - 26, cor, 3)
            img.linha(x0 + 1, by, x0 + 11, by - 26, borda, 1)
    # neblina rasteira
    for y in range(200, FH):
        a = int(70 * (y - 200) / (FH - 200))
        for x in range(FW):
            if BAYER4[y % 4][x % 4] < 10:
                img.set(x, y, (60, 30, 80, a))
    return img


FUNDOS = [
    ("lixao-ceu", fundo_ceu, 0.0),
    ("lixao-cidade-longe", fundo_cidade_longe, 0.06),
    ("lixao-cidade-perto", fundo_cidade_perto, 0.16),
    ("lixao-lixo-longe", fundo_lixo_longe, 0.32),
    ("lixao-lixo-perto", fundo_lixo_perto, 0.55),
]
