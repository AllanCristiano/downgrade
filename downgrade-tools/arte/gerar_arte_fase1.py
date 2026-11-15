"""DOWNGRADE — pixel art da Fase 1 (O Lixao).

Gera em <assets>/:
  tiles/lixao.png            tileset 32x32 (8 colunas)
  fundos/lixao-ceu.png       parallax 0   (960x544)
  fundos/lixao-cidade.png    parallax 0.15 (Torre Ofidia ao fundo)
  fundos/lixao-montes.png    parallax 0.4
  sprites/marco.png          32x48 x 16 quadros
  sprites/catador.png        32x48 x 7
  sprites/pistoleiro.png     32x48 x 4
  sprites/saida.png          32x80 x 2
  sprites/corte.png          48x48 x 3

Uso: python gerar_arte_fase1.py <pasta-assets> [pasta-preview]
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

from pixel import BAYER4, Img, escurecer, folha, misturar, texto

# =====================================================================  PALETA
K = (7, 1, 15)            # contorno
V0 = (13, 2, 33)          # fundo
V1 = (26, 11, 46)
V2 = (42, 27, 61)
V3 = (61, 42, 92)
V4 = (92, 61, 122)
CIANO = (0, 240, 255)
CIANO2 = (0, 140, 170)
ROSA = (255, 42, 109)
ROSA2 = (160, 20, 70)
LARANJA = (255, 140, 66)
LARANJA2 = (170, 80, 30)
AMARELO = (255, 209, 102)
VERDE = (61, 255, 154)
VERDE2 = (20, 140, 80)
BRANCO = (232, 230, 255)
PELE = (198, 136, 99)
PELE2 = (141, 90, 60)
FERRUGEM = (139, 74, 43)
FERRUGEM2 = (181, 101, 58)
FERRUGEM3 = (90, 45, 30)
METAL = (107, 107, 128)
METAL2 = (160, 160, 184)
METAL3 = (60, 60, 80)
TERRA = (58, 40, 52)
TERRA2 = (80, 56, 64)
TERRA3 = (40, 26, 40)
BORDA_NEON = (96, 40, 92)  # luz rosa da cidade batendo nas bordas


def alfa(c, a):
    return (c[0], c[1], c[2], a)


# =====================================================================  TILES
T = 32


def chao_meio(seed: int) -> Img:
    r = random.Random(seed)
    t = Img(T, T)
    t.rect(0, 0, T, T, TERRA3)
    for y in range(T):
        for x in range(T):
            v = r.random()
            if v < 0.14:
                t.set(x, y, TERRA)
            elif v < 0.17:
                t.set(x, y, V1)
    for _ in range(6):  # entulho enterrado
        x, y = r.randrange(T - 3), r.randrange(T - 2)
        t.rect(x, y, r.choice([2, 3]), 1, r.choice([METAL3, FERRUGEM3, V2]))
    for _ in range(2):  # caco de vidro brilhando
        t.set(r.randrange(T), r.randrange(T), r.choice([CIANO2, ROSA2]))
    return t


def chao_topo(seed: int, detalhe: str) -> Img:
    r = random.Random(seed)
    t = chao_meio(seed + 100)
    # contorno irregular da superficie (0..2 px)
    alturas = []
    h = 1
    for x in range(T):
        h = max(0, min(2, h + r.choice([-1, 0, 0, 1])))
        alturas.append(h)
    for x, h in enumerate(alturas):
        for y in range(h):
            t.set(x, y, None)
        t.set(x, h, BORDA_NEON)
        t.set(x, h + 1, TERRA2)
        if r.random() < 0.5:
            t.set(x, h + 2, TERRA)
    if detalhe == "lata":
        t.rect(9, 0, 4, 4, FERRUGEM2)
        t.rect(9, 0, 4, 1, METAL2)
        t.set(12, 1, FERRUGEM3)
        t.set(12, 2, FERRUGEM3)
    elif detalhe == "garrafa":
        t.rect(20, 1, 5, 2, alfa(CIANO2, 220))
        t.set(25, 1, CIANO)
        t.set(21, 1, alfa(BRANCO, 200))
    elif detalhe == "fio":
        for x in range(4, 18):
            y = 2 + round(math.sin(x * 0.8) * 1.2)
            t.set(x, y, METAL3)
        t.set(17, 2, LARANJA2)
    return t


def placa_metal(t: Img, borda_esq: bool, borda_dir: bool, seed: int) -> None:
    r = random.Random(seed)
    # chapa de cima
    t.rect(0, 0, T, 6, METAL)
    t.rect(0, 0, T, 1, METAL2)
    t.rect(0, 5, T, 1, METAL3)
    for x in range(4, T, 8):
        t.set(x, 3, K)
        t.set(x, 2, METAL2)
    # lataria corrugada enferrujada
    for y in range(6, T):
        for x in range(T):
            t.set(x, y, FERRUGEM if (x // 2) % 2 == 0 else FERRUGEM3)
    for _ in range(14):
        x, y = r.randrange(T), r.randrange(6, T)
        t.rect(x, y, 2, r.randrange(1, 4), FERRUGEM2)
    for _ in range(3):  # escorrido
        x = r.randrange(T)
        for y in range(6, 6 + r.randrange(4, 12)):
            t.set(x, y, TERRA3)
    t.rect(0, T - 2, T, 2, TERRA3)
    if borda_esq:
        t.rect(0, 0, 2, T, METAL3)
        t.rect(0, 0, 1, T, K)
    if borda_dir:
        t.rect(T - 2, 0, 2, T, METAL3)
        t.rect(T - 1, 0, 1, T, K)


def pneu(t: Img, cx: float, cy: float, r: float = 7) -> None:
    t.disco(cx, cy, r, K)
    t.anel(cx, cy, r - 3, r - 0.5, (30, 26, 34))
    for a in range(0, 360, 30):
        x = cx + math.cos(math.radians(a)) * (r - 1)
        y = cy + math.sin(math.radians(a)) * (r - 1)
        t.set(x, y, METAL3)
    t.disco(cx, cy, r - 3.5, V0)
    t.set(cx - r + 2, cy - r + 3, METAL)


def caixote(t: Img, x: int, y: int, w: int, h: int) -> None:
    t.rect(x, y, w, h, FERRUGEM)
    t.rect(x, y, w, 1, FERRUGEM2)
    for yy in range(y + 3, y + h, 4):
        t.rect(x, yy, w, 1, FERRUGEM3)
    t.rect(x, y, 1, h, FERRUGEM3)
    t.rect(x + w - 1, y, 1, h, FERRUGEM3)


def sucata(seed: int, topo: bool) -> Img:
    r = random.Random(seed)
    t = Img(T, T)
    t.rect(0, 0, T, T, V1)
    for _ in range(25):
        t.set(r.randrange(T), r.randrange(T), V2)
    caixote(t, 1, 14, 14, 12)
    pneu(t, 22, 22, 8)
    t.rect(4, 27, 20, 3, METAL3)  # cano
    t.rect(4, 27, 20, 1, METAL)
    pneu(t, 9, 8, 7)
    caixote(t, 18, 2, 12, 10)
    if topo:
        # silhueta no topo com borda neon
        for x in range(T):
            h = 1 + round(1.5 + 1.5 * math.sin(x * 0.45 + seed))
            for y in range(h):
                t.set(x, y, None)
            t.set(x, h, BORDA_NEON)
    return t


def caixa_perigo() -> Img:
    t = Img(T, T)
    t.rect(0, 0, T, T, METAL3)
    t.rect(2, 2, T - 4, T - 4, METAL)
    t.rect(2, 2, T - 4, 1, METAL2)
    for y in range(12, 20):
        for x in range(2, T - 2):
            t.set(x, y, AMARELO if ((x + y) // 3) % 2 == 0 else K)
    for x, y in ((4, 4), (27, 4), (4, 27), (27, 27)):
        t.set(x, y, K)
    return t


# ---- decoracao (camada sem colisao) ----

def deco_pneu() -> Img:
    t = Img(T, T)
    pneu(t, 16, 24, 7.5)
    return t


def deco_barril() -> Img:
    t = Img(T, T)
    x0, w, y0 = 10, 12, 13
    t.rect(x0, y0, w, T - y0, FERRUGEM)
    t.rect(x0, y0, 2, T - y0, FERRUGEM3)
    t.rect(x0 + w - 3, y0, 2, T - y0, FERRUGEM2)
    for y in (y0 + 4, y0 + 12):
        t.rect(x0, y, w, 1, FERRUGEM3)
    t.rect(x0, y0, w, 2, VERDE)  # liquido toxico
    t.rect(x0 + 2, y0, 4, 1, (180, 255, 210))
    for i, (x, y) in enumerate(((13, 11), (17, 9), (15, 6), (19, 12), (12, 8))):
        t.set(x, y, alfa(VERDE, 150 - i * 20))
    t.contorno(K)
    return t


def deco_tv(seed: int = 7) -> Img:
    r = random.Random(seed)
    t = Img(T, T)
    t.rect(7, 16, 18, 15, METAL3)
    t.rect(7, 16, 18, 1, METAL)
    t.rect(9, 18, 12, 10, K)
    for y in range(19, 27):
        for x in range(10, 20):
            t.set(x, y, r.choice([CIANO2, V3, BRANCO, CIANO2, V2]))
    t.rect(22, 19, 2, 2, ROSA2)
    t.rect(22, 23, 2, 1, METAL2)
    t.linha(13, 16, 9, 9, METAL2)
    t.linha(17, 16, 22, 10, METAL2)
    t.contorno(K)
    return t


def deco_saco() -> Img:
    t = Img(T, T)
    t.disco(16, 25, 7, (22, 18, 30))
    t.disco(13, 22, 4, (32, 26, 44))
    t.rect(15, 16, 3, 3, (22, 18, 30))
    t.set(16, 15, (40, 34, 56))
    t.set(12, 20, V3)
    t.contorno(K)
    return t


def deco_placa() -> list[Img]:
    """Letreiro neon ATERRO 9 (3 tiles)."""
    p = Img(T * 3, T)
    p.rect(6, 3, 84, 21, K)
    p.rect(6, 3, 84, 1, CIANO2)
    p.rect(6, 23, 84, 1, CIANO2)
    p.rect(6, 3, 1, 21, CIANO2)
    p.rect(89, 3, 1, 21, CIANO2)
    # brilho do neon (borda borrada)
    glow = Img(T * 3, T)
    texto(glow, 17, 8, "ATERRO 9", alfa(ROSA, 70), 2)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        p.colar(glow, dx, dy)
    texto(p, 17, 8, "ATERRO 9", ROSA, 2, {3: ROSA2})  # um R queimado
    p.rect(14, 24, 2, 8, METAL3)
    p.rect(80, 24, 2, 8, METAL3)
    return [_recorte(p, i * T, 0) for i in range(3)]


def deco_cadaver() -> list[Img]:
    """O corpo de Helena no lixao (2 tiles). A nuca ainda brilha onde estava a Escama."""
    c = Img(T * 2, T)
    chao = 31
    # poca escura
    for x in range(14, 58):
        c.set(x, chao, (50, 8, 30))
    c.rect(20, chao - 1, 30, 1, (50, 8, 30))
    # pernas
    c.rect(6, chao - 5, 16, 3, (40, 40, 58))
    c.rect(6, chao - 3, 14, 2, (30, 30, 44))
    c.rect(3, chao - 6, 4, 4, (36, 26, 22))  # botas
    # jaleco/casaco longo
    c.rect(20, chao - 8, 22, 7, (70, 72, 90))
    c.rect(20, chao - 8, 22, 1, (110, 112, 135))
    c.rect(24, chao - 4, 12, 2, (50, 52, 66))
    # braco estendido
    c.rect(30, chao - 10, 12, 2, (70, 72, 90))
    c.rect(41, chao - 11, 3, 2, PELE2)
    # cabeca e cabelo espalhado
    c.disco(47, chao - 5, 4, PELE2)
    c.rect(45, chao - 9, 13, 3, (24, 14, 22))
    c.rect(50, chao - 6, 9, 3, (24, 14, 22))
    c.rect(56, chao - 3, 4, 2, (24, 14, 22))
    c.contorno(K)
    # brilho ciano na nuca (onde estava a Escama)
    c.set(44, chao - 3, CIANO)
    for x, y, a in ((43, chao - 3, 140), (45, chao - 3, 140), (44, chao - 4, 140), (44, chao - 2, 120), (42, chao - 3, 60)):
        c.set(x, y, alfa(CIANO, a))
    return [_recorte(c, 0, 0), _recorte(c, T, 0)]


def deco_poste() -> list[Img]:
    topo, meio = Img(T, T), Img(T, T)
    topo.rect(6, 6, 3, 26, METAL3)
    topo.rect(6, 6, 1, 26, METAL)
    topo.rect(6, 5, 18, 2, METAL3)
    topo.rect(20, 7, 7, 3, METAL)
    topo.rect(21, 10, 5, 1, AMARELO)
    topo.contorno(K)
    for i in range(1, 22):  # cone de luz
        w = 2 + i // 2
        for x in range(23 - w // 2, 23 + w // 2 + 1):
            topo.set(x, 10 + i, alfa(AMARELO, max(10, 60 - i * 2)))
    meio.rect(6, 0, 3, T, METAL3)
    meio.rect(6, 0, 1, T, METAL)
    meio.rect(5, T - 3, 5, 3, METAL3)
    meio.contorno(K)
    for i in range(T):
        w = 13 + i // 2
        for x in range(23 - w // 2, 23 + w // 2 + 1):
            if x > 9:
                meio.set(x, i, alfa(AMARELO, max(6, 18 - i // 2)))
    return [topo, meio]


def _recorte(img: Img, x: int, y: int) -> Img:
    t = Img(T, T)
    for yy in range(T):
        for xx in range(T):
            t.px[yy][xx] = img.get(x + xx, y + yy)
    return t


# Ordem = ids no Tiled (firstgid 1)
NOMES_TILES = [
    "chao_topo_a", "chao_topo_b", "chao_topo_c", "chao_meio_a", "chao_meio_b", "plat_esq", "plat_meio", "plat_dir",
    "plat_unica", "sucata_topo", "sucata_meio", "caixa", "pneu", "barril", "tv", "saco",
    "placa_1", "placa_2", "placa_3", "cadaver_1", "cadaver_2", "poste_topo", "poste_meio", "vazio",
]


def gerar_tileset() -> Img:
    tiles: dict[str, Img] = {
        "chao_topo_a": chao_topo(1, "lata"),
        "chao_topo_b": chao_topo(2, "garrafa"),
        "chao_topo_c": chao_topo(3, "fio"),
        "chao_meio_a": chao_meio(4),
        "chao_meio_b": chao_meio(5),
        "sucata_topo": sucata(6, True),
        "sucata_meio": sucata(7, False),
        "caixa": caixa_perigo(),
        "pneu": deco_pneu(),
        "barril": deco_barril(),
        "tv": deco_tv(),
        "saco": deco_saco(),
        "vazio": Img(T, T),
    }
    for nome, esq, dir_ in (("plat_esq", True, False), ("plat_meio", False, False), ("plat_dir", False, True), ("plat_unica", True, True)):
        t = Img(T, T)
        placa_metal(t, esq, dir_, hash(nome) % 1000)
        tiles[nome] = t
    tiles["placa_1"], tiles["placa_2"], tiles["placa_3"] = deco_placa()
    tiles["cadaver_1"], tiles["cadaver_2"] = deco_cadaver()
    tiles["poste_topo"], tiles["poste_meio"] = deco_poste()

    cols = 8
    linhas = math.ceil(len(NOMES_TILES) / cols)
    ts = Img(cols * T, linhas * T)
    for i, nome in enumerate(NOMES_TILES):
        ts.colar(tiles[nome], (i % cols) * T, (i // cols) * T)
    return ts


# =====================================================================  FUNDOS
FW, FH = 960, 544


def fundo_ceu() -> Img:
    r = random.Random(11)
    img = Img(FW, FH)
    faixas = [(0, (8, 2, 20)), (0.35, V0), (0.6, V1), (0.78, (48, 14, 62)), (0.9, (78, 22, 84)), (1, (110, 30, 96))]
    for y in range(FH):
        t = y / FH
        for i in range(len(faixas) - 1):
            if faixas[i][0] <= t <= faixas[i + 1][0]:
                t0, c0 = faixas[i]
                t1, c1 = faixas[i + 1]
                local = (t - t0) / (t1 - t0)
                break
        for x in range(FW):
            limiar = (BAYER4[y % 4][x % 4] + 0.5) / 16
            img.px[y][x] = c1 if local > limiar else c0
    # estrelas apagadas pelo smog
    for _ in range(90):
        x, y = r.randrange(FW), r.randrange(int(FH * 0.45))
        img.set(x, y, r.choice([V3, V4, (140, 120, 170)]))
    # nuvens de smog
    for _ in range(9):
        cx, cy = r.randrange(FW), r.randrange(60, 300)
        w, h = r.randrange(120, 260), r.randrange(6, 14)
        for y in range(cy, cy + h):
            recuo = abs(y - cy - h / 2) * 4
            for x in range(int(cx - w / 2 + recuo), int(cx + w / 2 - recuo)):
                if (BAYER4[y % 4][x % 4]) < 11:
                    img.set(x % FW, y, (32, 14, 50))
            img.set((cx - w / 2 + recuo) % FW, cy + h - 1, (70, 30, 80))
    return img


def fundo_cidade() -> Img:
    r = random.Random(21)
    img = Img(FW, FH)
    base = FH
    silh, silh_borda = (30, 14, 52), (46, 24, 74)

    def predio(x0: int, w: int, h: int, cor, borda, janelas: float) -> None:
        topo = base - h
        for x in range(x0, x0 + w):
            for y in range(topo, base):
                img.set(x % FW, y, cor)
            img.set(x % FW, topo, borda)
        for y in range(topo, base):
            img.set(x0 % FW, y, borda)
        for y in range(topo + 6, base - 4, 6):
            for x in range(x0 + 3, x0 + w - 3, 4):
                if r.random() < janelas:
                    c = r.choice([(30, 110, 130), (140, 30, 80), (150, 120, 60), (40, 90, 110)])
                    img.set(x % FW, y, c)
                    img.set(x % FW, y + 1, escurecer(c, 0.7))
        if r.random() < 0.5:  # antena com luz
            ax = x0 + w // 2
            for y in range(topo - r.randrange(8, 20), topo):
                img.set(ax % FW, y, borda)
            img.set(ax % FW, topo - 20, ROSA)

    # camada de tras (mais escura e baixa)
    x = 0
    while x < FW:
        w = r.randrange(24, 60)
        predio(x, w, r.randrange(120, 230), (24, 10, 42), (36, 18, 60), 0.12)
        x += w + r.randrange(0, 6)
    # camada da frente
    x = 10
    while x < FW:
        w = r.randrange(30, 80)
        if not 560 < x < 700:
            predio(x, w, r.randrange(160, 300), silh, silh_borda, 0.22)
        x += w + r.randrange(4, 20)

    # TORRE OFIDIA
    tx, tw = 610, 50
    topo = base - 470
    for y in range(topo, base):
        recuo = 0 if y > topo + 60 else (6 if y > topo + 25 else 14)
        for xx in range(tx + recuo, tx + tw - recuo):
            img.set(xx, y, (22, 10, 40))
        img.set(tx + recuo, y, (40, 30, 80))
        img.set(tx + tw - recuo - 1, y, CIANO2 if y % 3 else (20, 70, 90))
    for y in range(topo + 70, base, 5):  # faixas de luz verticais
        img.set(tx + 16, y, (20, 90, 110))
        img.set(tx + 33, y, (20, 90, 110))
    for y in range(topo - 40, topo):  # antena
        img.set(tx + tw // 2, y, (40, 30, 80))
    img.set(tx + tw // 2, topo - 41, ROSA)
    # emblema: escama (losango) holografico
    ex, ey = tx + tw // 2, topo + 42
    for dy in range(-16, 17):
        largura = 12 - abs(dy) * 12 // 16
        for dx in range(-largura, largura + 1):
            borda = abs(dx) == largura or abs(dy) == 16
            a = 230 if borda else (60 if (dy // 3) % 2 == 0 else 25)
            img.set(ex + dx, ey + dy, (CIANO[0], CIANO[1], CIANO[2], a))
    for dx in range(-20, 21):  # halo
        for dy in range(-22, 23):
            d = math.hypot(dx, dy * 0.8)
            if 18 < d < 24 and BAYER4[(ey + dy) % 4][(ex + dx) % 4] < 4:
                img.set(ex + dx, ey + dy, (0, 140, 170, 120))
    texto(img, tx + 6, topo + 64, "OFIDIA", (0, 200, 220), 1)
    return img


def fundo_montes() -> Img:
    r = random.Random(31)
    img = Img(FW, FH)
    escuro, borda = (18, 7, 30), (90, 34, 96)

    def altura(x: int) -> int:
        p = 2 * math.pi * x / FW
        return round(395 + 32 * math.sin(2 * p + 1) + 18 * math.sin(5 * p + 2) + 6 * math.sin(13 * p))

    tops = [altura(x) for x in range(FW)]
    for x in range(FW):
        for y in range(tops[x], FH):
            img.px[y][x] = escuro
        img.set(x, tops[x], borda)
        if r.random() < 0.3:
            img.set(x, tops[x] + 1, (50, 18, 60))

    def silhueta_rect(x0, w, h, inclina=0):
        base_y = tops[x0 % FW] + 3
        for i in range(w):
            for y in range(base_y - h + (i * inclina) // max(1, w), base_y):
                img.set((x0 + i) % FW, y, escuro)
            img.set((x0 + i) % FW, base_y - h + (i * inclina) // max(1, w), borda)

    # carros, geladeiras, canos espetados
    for _ in range(14):
        x0 = r.randrange(FW)
        silhueta_rect(x0, r.randrange(8, 30), r.randrange(6, 18), r.choice([-6, 0, 4]))
    # guindaste
    gx = 240
    gy = tops[gx]
    img.linha(gx, gy, gx + 6, gy - 120, escuro, 4)
    img.linha(gx + 6, gy - 120, gx + 120, gy - 100, escuro, 3)
    img.linha(gx + 6, gy - 121, gx + 120, gy - 101, borda, 1)
    img.linha(gx + 110, gy - 100, gx + 110, gy - 60, (40, 20, 50), 1)
    img.rect(gx + 104, gy - 60, 12, 8, escuro)
    img.set(gx + 6, gy - 124, ROSA)
    # fogueiras dos catadores
    for _ in range(6):
        x = r.randrange(FW)
        y = tops[x] + r.randrange(8, 40)
        img.set(x, y, LARANJA)
        img.set(x, y - 1, AMARELO)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -2), (1, -1), (-1, -1)):
            img.set(x + dx, y + dy, alfa(LARANJA, 110))
    return img


# =====================================================================  PERSONAGENS
SW, SH = 32, 48


class Pose:
    def __init__(self, **kw):
        self.bob = 0          # px para baixo
        self.agacha = 0
        self.inclina = 0      # ombros para frente
        self.quadril_f = 0    # angulos em graus: 0 = para baixo, 90 = para frente, 180 = para cima
        self.joelho_f = 0     # dobra do joelho (para tras)
        self.quadril_t = 0
        self.joelho_t = 0
        self.ombro_f = 10
        self.cotovelo_f = 10  # dobra do cotovelo (para frente)
        self.ombro_t = -10
        self.cotovelo_t = 10
        self.cabeca_baixa = 0
        self.cachecol = 0     # fase da animacao do cachecol
        self.extra = None     # acao especial (lamina, cano, arma, clarão)
        self.__dict__.update(kw)


def membro(img: Img, x: float, y: float, ang: float, comp: float, cor, esp: int):
    rad = math.radians(ang)
    x1, y1 = x + math.sin(rad) * comp, y + math.cos(rad) * comp
    img.linha(x, y, x1, y1, cor, esp)
    return x1, y1


def humano(p: Pose, e: dict) -> Img:
    img = Img(SW, SH)
    qx, qy = 15, 30 + p.bob + p.agacha
    ox, oy = 15 + p.inclina, 19 + p.bob + p.agacha
    tw = e.get("largura", 8)
    maos = {}

    def braco(frente: bool):
        sh, el = (p.ombro_f, p.cotovelo_f) if frente else (p.ombro_t, p.cotovelo_t)
        cor = e["jaqueta"] if frente else e["jaqueta2"]
        sx = ox + (1 if frente else -1)
        cx, cy = membro(img, sx, oy + 1, sh, 6, cor, 3 if e.get("bracos_grossos") else 2)
        hx, hy = membro(img, cx, cy, sh + el, 6, cor, 2)
        img.rect(round(hx) - 1, round(hy) - 1, 2, 2, e["pele"] if frente else e["pele2"])
        maos["frente" if frente else "tras"] = (hx, hy, sh + el)

    def perna(frente: bool):
        hp, kn = (p.quadril_f, p.joelho_f) if frente else (p.quadril_t, p.joelho_t)
        cor = e["calca"] if frente else e["calca2"]
        jx, jy = membro(img, qx + (1 if frente else -1), qy, hp, 8, cor, 3)
        ax, ay = membro(img, jx, jy, hp - kn, 8, cor, 3)
        bx, by = round(ax), round(ay)
        img.rect(bx - 1, by - 1, 4, 3, e["bota"] if frente else escurecer(e["bota"], 0.7))
        img.rect(bx - 1, by + 1, 4, 1, escurecer(e["bota"], 0.5))

    braco(False)
    perna(False)
    # tronco
    for y in range(oy, qy + 1):
        t = (y - oy) / max(1, qy - oy)
        cx = round(ox + (qx - ox) * t)
        for x in range(cx - tw // 2, cx + tw // 2):
            img.set(x, y, e["jaqueta"])
        img.set(cx - tw // 2, y, e["jaqueta2"])
        img.set(cx - tw // 2 + 1, y, e["jaqueta2"])
        img.set(cx + tw // 2 - 1, y, e["jaqueta_luz"])
    img.rect(qx - tw // 2, qy - 1, tw, 1, escurecer(e["calca"], 0.8))  # cinto
    if "detalhe_tronco" in e:
        e["detalhe_tronco"](img, ox, oy, qx, qy, p)
    perna(True)
    # cabeca
    hx, hy = ox - 3, oy - 9 + p.cabeca_baixa
    img.rect(ox - 1, oy - 2, 3, 2, e["pele2"])  # pescoco
    img.rect(hx, hy + 1, 7, 7, e["pele"])
    img.rect(hx + 1, hy, 5, 1, e["pele"])
    img.rect(hx, hy + 6, 2, 2, e["pele2"])
    img.set(hx + 5, hy + 3, e.get("olho", K))
    e["cabeca"](img, hx, hy, p)
    braco(True)
    if p.extra and "acao" in e:
        e["acao"](img, maos, p)
    img.contorno(K)
    if "brilho" in e:
        e["brilho"](img, hx, hy, ox, oy, maos, p)
    return img


# ---- MARCO ----

def marco_cabeca(img, hx, hy, p):
    cab = (30, 20, 36)
    img.rect(hx, hy - 1, 6, 2, cab)
    img.rect(hx - 1, hy, 3, 5, cab)
    img.set(hx + 2, hy - 2, cab)
    img.set(hx + 4, hy - 2, cab)
    img.set(hx + 6, hy, cab)
    img.set(hx - 2, hy + 1, cab)


def marco_tronco(img, ox, oy, qx, qy, p):
    # cachecol vermelho tremulando para tras
    img.rect(ox - 3, oy, 7, 2, ROSA2)
    onda = [0, 1, 1, 0, -1, -1][p.cachecol % 6]
    for i in range(1, 6):
        img.set(ox - 3 - i, oy + 1 + (i // 2) + (onda if i > 2 else 0), ROSA2 if i < 4 else (120, 15, 55))
        img.set(ox - 3 - i, oy + (i // 2) + (onda if i > 2 else 0), ROSA2)
    # listra ciano na jaqueta
    for y in range(oy + 3, qy - 2):
        img.set(ox + 1 + round((qx - ox) * (y - oy) / max(1, qy - oy)), y, (20, 120, 140))


def marco_acao(img, maos, p):
    if p.extra == "lamina":
        hx, hy, ang = maos["frente"]
        x, y = hx, hy
        for i in range(14):
            x += math.sin(math.radians(ang))
            y += math.cos(math.radians(ang))
            img.set(x, y, BRANCO if i % 3 else CIANO)
    elif p.extra == "lamina_curta":
        hx, hy, ang = maos["frente"]
        membro(img, hx, hy, ang, 6, CIANO, 1)


def marco_brilho(img, hx, hy, ox, oy, maos, p):
    # a Escama na nuca
    x, y = hx, hy + 7
    img.set(x, y, CIANO)
    for dx, dy in ((-1, 0), (0, -1), (0, 1)):
        img.set(x + dx, y + dy, alfa(CIANO, 110))
    if p.extra == "lamina":
        hx2, hy2, ang = maos["frente"]
        xx, yy = hx2, hy2
        for i in range(14):
            xx += math.sin(math.radians(ang))
            yy += math.cos(math.radians(ang))
            for dx, dy in ((0, -1), (0, 1)):
                img.set(xx + dx, yy + dy, alfa(CIANO, 90))


MARCO = {
    "pele": PELE, "pele2": PELE2, "olho": K,
    "jaqueta": (24, 70, 92), "jaqueta2": (14, 44, 60), "jaqueta_luz": (44, 118, 138),
    "calca": (43, 37, 64), "calca2": (30, 25, 46), "bota": (70, 48, 34),
    "cabeca": marco_cabeca, "detalhe_tronco": marco_tronco, "acao": marco_acao, "brilho": marco_brilho,
}


def quadros_marco() -> list[Img]:
    q = []
    for i in range(4):  # 0-3 parado (respirando)
        q.append(humano(Pose(bob=[0, 0, 1, 1][i], quadril_f=6, quadril_t=-6, joelho_f=4, joelho_t=4,
                             ombro_f=8, ombro_t=-8, cachecol=i), MARCO))
    for i in range(6):  # 4-9 correndo
        t = 2 * math.pi * i / 6
        q.append(humano(Pose(
            bob=-1 if abs(math.sin(t)) < 0.6 else 0, inclina=2,
            quadril_f=38 * math.sin(t), quadril_t=38 * math.sin(t + math.pi),
            joelho_f=10 + 55 * max(0, math.cos(t)), joelho_t=10 + 55 * max(0, math.cos(t + math.pi)),
            ombro_f=-35 * math.sin(t), cotovelo_f=60, ombro_t=35 * math.sin(t), cotovelo_t=60, cachecol=i,
        ), MARCO))
    q.append(humano(Pose(quadril_f=55, joelho_f=80, quadril_t=15, joelho_t=60, ombro_f=150, cotovelo_f=-20,
                         ombro_t=-60, cotovelo_t=30, bob=-2, cachecol=1), MARCO))          # 10 subindo
    q.append(humano(Pose(quadril_f=25, joelho_f=25, quadril_t=-15, joelho_t=35, ombro_f=115, cotovelo_f=10,
                         ombro_t=-110, cotovelo_t=-10, cachecol=4), MARCO))                 # 11 caindo
    q.append(humano(Pose(inclina=-1, quadril_f=20, quadril_t=-15, joelho_f=10, joelho_t=10, ombro_f=-150,
                         cotovelo_f=-30, ombro_t=-20, cachecol=2), MARCO))                  # 12 preparo
    q.append(humano(Pose(inclina=3, quadril_f=30, quadril_t=-25, joelho_f=15, joelho_t=10, ombro_f=85,
                         cotovelo_f=0, ombro_t=-40, extra="lamina", cachecol=3), MARCO))    # 13 corte
    q.append(humano(Pose(inclina=2, quadril_f=25, quadril_t=-20, joelho_f=10, joelho_t=10, ombro_f=40,
                         cotovelo_f=25, ombro_t=-30, extra="lamina_curta", cachecol=4), MARCO))  # 14 fim do corte
    q.append(humano(Pose(agacha=7, inclina=4, cabeca_baixa=2, quadril_f=85, joelho_f=160, quadril_t=40,
                         joelho_t=150, ombro_f=5, cotovelo_f=0, ombro_t=-5, cachecol=0), MARCO))  # 15 morto
    return q


# ---- CATADOR ----

def catador_cabeca(img, hx, hy, p):
    img.rect(hx - 1, hy - 1, 8, 3, ROSA2)  # bandana
    img.rect(hx - 3, hy + 1, 3, 2, ROSA2)
    img.rect(hx + 3, hy + 3, 4, 2, (60, 20, 40))  # oculos


def catador_tronco(img, ox, oy, qx, qy, p):
    for y in range(oy + 2, qy, 3):  # remendos
        img.set(ox - 1, y, (70, 46, 30))
        img.set(ox + 2, y + 1, (120, 85, 55))


def catador_acao(img, maos, p):
    hx, hy, ang = maos["frente"]
    a = ang + (p.extra == "cano_cima") * 0
    membro(img, hx, hy, a, 11, METAL2, 2)
    membro(img, hx, hy, a - 180, 3, METAL3, 2)


def catador_brilho(img, hx, hy, ox, oy, maos, p):
    for x in range(hx + 3, hx + 7):  # oculos neon
        img.set(x, hy + 3, ROSA)
    img.set(hx + 7, hy + 3, alfa(ROSA, 120))


CATADOR = {
    "pele": PELE2, "pele2": (110, 70, 48), "olho": ROSA,
    "jaqueta": (92, 62, 40), "jaqueta2": (62, 40, 27), "jaqueta_luz": (125, 88, 56),
    "calca": (56, 52, 42), "calca2": (40, 36, 30), "bota": (45, 34, 28),
    "largura": 10, "bracos_grossos": True,
    "cabeca": catador_cabeca, "detalhe_tronco": catador_tronco, "acao": catador_acao, "brilho": catador_brilho,
}


def quadros_catador() -> list[Img]:
    q = []
    for i in range(4):  # 0-3 andando
        t = 2 * math.pi * i / 4
        q.append(humano(Pose(
            inclina=3, bob=1 if i % 2 else 0,
            quadril_f=24 * math.sin(t), quadril_t=24 * math.sin(t + math.pi),
            joelho_f=10 + 30 * max(0, math.cos(t)), joelho_t=10 + 30 * max(0, math.cos(t + math.pi)),
            ombro_f=35, cotovelo_f=35, ombro_t=-15 * math.sin(t), cotovelo_t=30, extra="cano",
        ), CATADOR))
    q.append(humano(Pose(inclina=0, quadril_f=15, quadril_t=-15, ombro_f=-160, cotovelo_f=-40, ombro_t=-30,
                         extra="cano"), CATADOR))                                            # 4 preparando
    q.append(humano(Pose(inclina=5, agacha=1, quadril_f=35, joelho_f=20, quadril_t=-25, ombro_f=100,
                         cotovelo_f=-5, ombro_t=-50, extra="cano"), CATADOR))               # 5 golpe
    q.append(humano(Pose(inclina=3, quadril_f=5, quadril_t=-5, ombro_f=35, cotovelo_f=35, ombro_t=-10,
                         extra="cano"), CATADOR))                                            # 6 parado
    return q


# ---- PISTOLEIRO ----

def pistoleiro_cabeca(img, hx, hy, p):
    img.rect(hx - 1, hy - 1, 8, 3, (30, 26, 40))  # bone
    img.rect(hx + 5, hy + 1, 4, 1, (30, 26, 40))   # aba
    img.set(hx + 2, hy, LARANJA)
    img.rect(hx - 1, hy + 2, 2, 3, (40, 26, 22))


def pistoleiro_acao(img, maos, p):
    hx, hy, ang = maos["frente"]
    x, y = round(hx), round(hy)
    if ang > 60:  # mirando para frente
        img.rect(x, y - 2, 6, 2, K)
        img.rect(x, y, 2, 2, K)
        img.set(x + 4, y - 2, LARANJA)
    else:
        img.rect(x - 1, y, 2, 5, K)


def pistoleiro_brilho(img, hx, hy, ox, oy, maos, p):
    if p.extra == "tiro":
        x, y = round(maos["frente"][0]) + 7, round(maos["frente"][1]) - 1
        img.rect(x, y - 1, 2, 3, AMARELO)
        img.set(x + 2, y, BRANCO)
        for dx, dy in ((0, -2), (0, 2), (2, -1), (2, 1), (3, 0)):
            img.set(x + dx, y + dy, alfa(AMARELO, 130))


PISTOLEIRO = {
    "pele": PELE, "pele2": PELE2, "olho": K,
    "jaqueta": LARANJA2, "jaqueta2": (120, 55, 20), "jaqueta_luz": LARANJA,
    "calca": (40, 40, 56), "calca2": (28, 28, 40), "bota": (30, 26, 30),
    "cabeca": pistoleiro_cabeca, "acao": pistoleiro_acao, "brilho": pistoleiro_brilho,
}


def quadros_pistoleiro() -> list[Img]:
    return [
        humano(Pose(quadril_f=8, quadril_t=-8, ombro_f=10, cotovelo_f=15, ombro_t=-8, extra="arma"), PISTOLEIRO),
        humano(Pose(bob=1, quadril_f=8, quadril_t=-8, ombro_f=10, cotovelo_f=15, ombro_t=-8, extra="arma"), PISTOLEIRO),
        humano(Pose(quadril_f=15, quadril_t=-15, ombro_f=90, cotovelo_f=0, ombro_t=-20, extra="arma"), PISTOLEIRO),
        humano(Pose(inclina=-1, quadril_f=15, quadril_t=-15, ombro_f=95, cotovelo_f=0, ombro_t=-20, extra="tiro"),
               PISTOLEIRO),
    ]


# ---- SAIDA (porta de correr) ----

def quadros_saida() -> list[Img]:
    q = []
    for aberta in (False, True):
        s = Img(32, 80)
        s.rect(0, 6, 32, 74, METAL3)
        s.rect(0, 6, 32, 1, METAL)
        s.rect(3, 10, 26, 70, K)
        if aberta:
            for y in range(10, 80):
                a = round(40 + 140 * (y - 10) / 70)
                s.rect(3, y, 26, 1, (VERDE2[0], VERDE2[1], VERDE2[2], a))
            s.rect(3, 10, 26, 10, METAL)
            for y in range(12, 20, 3):
                s.rect(3, y, 26, 1, METAL3)
            luz = VERDE
        else:
            s.rect(3, 10, 26, 70, METAL)
            for y in range(14, 74, 8):
                s.rect(3, y, 26, 1, METAL3)
                s.rect(3, y + 1, 26, 1, METAL2)
            for y in range(74, 80):
                for x in range(3, 29):
                    s.set(x, y, AMARELO if ((x + y) // 3) % 2 == 0 else K)
            luz = ROSA
        s.rect(12, 0, 8, 5, K)
        s.rect(13, 1, 6, 3, luz)
        for dx in range(-2, 10):
            s.set(13 + dx, 5, (luz[0], luz[1], luz[2], 90))
        q.append(s)
    return q


# ---- CORTE (efeito da Espada) ----

def quadros_corte() -> list[Img]:
    q = []
    for f in range(3):
        c = Img(48, 48)
        cx, cy = 10, 24
        r0, r1 = [(12, 22), (16, 22), (19, 22)][f]
        lim = [80, 70, 60][f]
        for y in range(48):
            for x in range(48):
                d = math.hypot(x - cx, y - cy)
                ang = math.degrees(math.atan2(y - cy, x - cx))
                if r0 <= d <= r1 and abs(ang) <= lim:
                    borda = d > r1 - 1.5
                    if f == 0:
                        cor = BRANCO if borda else (CIANO[0], CIANO[1], CIANO[2], 200)
                    elif f == 1:
                        cor = CIANO if borda else (CIANO[0], CIANO[1], CIANO[2], 120)
                    else:
                        cor = (CIANO[0], CIANO[1], CIANO[2], 150 if borda else 50)
                    c.set(x, y, cor)
        q.append(c)
    return q


# =====================================================================  MAIN

def main() -> None:
    assets = Path(sys.argv[1])
    preview = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    ts = gerar_tileset()
    ts.salvar(assets / "tiles" / "lixao.png")

    ceu, cidade, montes = fundo_ceu(), fundo_cidade(), fundo_montes()
    ceu.salvar(assets / "fundos" / "lixao-ceu.png")
    cidade.salvar(assets / "fundos" / "lixao-cidade.png")
    montes.salvar(assets / "fundos" / "lixao-montes.png")

    folhas = {
        "marco": folha(quadros_marco()),
        "catador": folha(quadros_catador()),
        "pistoleiro": folha(quadros_pistoleiro()),
        "saida": folha(quadros_saida()),
        "corte": folha(quadros_corte()),
    }
    for nome, f in folhas.items():
        f.salvar(assets / "sprites" / f"{nome}.png")

    if preview:
        preview.mkdir(parents=True, exist_ok=True)
        ts.escalar(3).salvar(preview / "tileset-x3.png")
        sprites = Img(560, 260)
        sprites.rect(0, 0, 560, 260, V1)
        sprites.colar(folhas["marco"], 0, 0)
        sprites.colar(folhas["catador"], 0, 52)
        sprites.colar(folhas["pistoleiro"], 240, 52)
        sprites.colar(folhas["saida"], 380, 52)
        sprites.colar(folhas["corte"], 0, 140)
        sprites.escalar(3).salvar(preview / "sprites-x3.png")
        cena = Img(FW, FH)
        for camada in (ceu, cidade, montes):
            cena.colar(camada, 0, 0)
        cena.salvar(preview / "fundo.png")
    print("arte gerada em", assets)


if __name__ == "__main__":
    main()
