"""Personagens de DOWNGRADE: esqueleto (rig) + poses + animacoes.

Quadros de 64x64, personagem olhando para a DIREITA, pes na base (y=63).
Angulos dos membros em graus: 0 = para baixo, 90 = para frente, 180 = para cima, -90 = para tras.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, fields, replace

from pixel import Img, alfa

Q = 64  # tamanho do quadro
K = (10, 4, 18)  # contorno
NEON_BORDA = (255, 96, 176)


def rampa(*cores):
    return list(cores)


# ---------------------------------------------------------------- rampas (sombra -> brilho, com hue shift)
PELE = rampa((84, 42, 52), (146, 86, 72), (198, 130, 98), (238, 182, 142))
PELE_ESCURA = rampa((60, 30, 40), (112, 64, 54), (156, 98, 72), (196, 140, 104))
CABELO = rampa((14, 8, 22), (32, 20, 44), (56, 38, 72), (92, 70, 116))
JAQUETA_MARCO = rampa((12, 22, 42), (20, 50, 74), (32, 88, 110), (74, 152, 164))
CALCA_MARCO = rampa((18, 16, 32), (36, 32, 58), (58, 52, 86), (88, 80, 118))
BOTA = rampa((22, 14, 20), (48, 30, 32), (82, 56, 48), (124, 92, 72))
LUVA = rampa((18, 18, 26), (38, 38, 52), (62, 62, 80), (98, 98, 116))
CACHECOL = rampa((76, 8, 34), (152, 20, 60), (222, 44, 92), (255, 116, 146))
CIANO = (0, 240, 255)
BRANCO = (240, 250, 255)

TRAPO = rampa((40, 26, 22), (78, 52, 38), (112, 80, 56), (150, 114, 80))
TRAPO2 = rampa((34, 34, 30), (62, 60, 50), (92, 88, 70), (126, 120, 96))
CAPUZ = rampa((30, 20, 24), (58, 40, 40), (88, 62, 56), (120, 92, 78))
MASCARA = rampa((26, 26, 34), (56, 56, 70), (96, 96, 112), (150, 150, 168))
METAL = rampa((30, 30, 42), (70, 70, 88), (122, 122, 142), (186, 186, 204))
ROSA = (255, 42, 109)

JAQUETA_PIST = rampa((70, 26, 16), (150, 62, 20), (214, 108, 42), (255, 168, 92))
GOLA = rampa((80, 66, 52), (136, 116, 90), (186, 166, 132), (226, 212, 180))
CALCA_PIST = rampa((16, 18, 30), (34, 38, 58), (56, 62, 88), (86, 94, 124))
BONE = rampa((14, 12, 20), (30, 28, 40), (52, 48, 66), (84, 78, 100))
ARMA = rampa((8, 8, 12), (28, 28, 36), (54, 54, 66), (110, 110, 126))
OURO = (255, 200, 90)
CANHAO = rampa((26, 22, 30), (60, 52, 58), (104, 92, 86), (160, 146, 120))
AMARELO = (255, 209, 102)


@dataclass
class Pose:
    x: float = 0
    y: float = 0
    incl: float = 0          # inclinacao do tronco (+ = para frente)
    bf: tuple = (15, 15)     # braco da frente (ombro, cotovelo)
    bt: tuple = (-15, 15)    # braco de tras
    pf: tuple = (8, 6)       # perna da frente (quadril, joelho)
    pt: tuple = (-8, 6)      # perna de tras
    vento: float = 0.5       # forca do vento no cachecol
    vento_dir: float = 0     # direcao do cachecol: 0 = para tras, + = para baixo, - = para cima
    fase: float = 0
    arma: str = ""
    arma_ang: float | None = None
    brilho: float = 1.0      # pulso da Escama / olhos neon
    clarao: bool = False     # clarao de tiro


def lerp_pose(a: Pose, b: Pose, t: float) -> Pose:
    kw = {}
    for f in fields(Pose):
        va, vb = getattr(a, f.name), getattr(b, f.name)
        if isinstance(va, tuple):
            kw[f.name] = tuple(x + (y - x) * t for x, y in zip(va, vb))
        elif isinstance(va, (int, float)) and isinstance(vb, (int, float)) and not isinstance(va, bool):
            kw[f.name] = va + (vb - va) * t
        else:
            kw[f.name] = vb if t >= 0.5 else va
    return Pose(**kw)


def dirv(ang: float) -> tuple[float, float]:
    r = math.radians(ang)
    return math.sin(r), math.cos(r)


def soma(p, v, k=1.0):
    return p[0] + v[0] * k, p[1] + v[1] * k


# ======================================================================== RIG

class Estilo:
    """Define a aparencia de um personagem. Subclasses desenham cabeca, roupa e arma."""
    largura_quadril = 4.4
    largura_peito = 5.6
    calca = CALCA_MARCO
    jaqueta = JAQUETA_MARCO
    luva = LUVA
    bota = BOTA
    pele = PELE
    rim = None  # luz de borda aplicada no final, so na silhueta (ver luz_de_borda)

    def cachecol_tras(self, img, g, p): ...
    def roupa(self, img, g, p): ...
    def cabeca(self, img, g, p): ...
    def arma(self, img, g, p): ...
    def brilhos(self, img, g, p): ...


class Geo:
    """Pontos calculados do esqueleto para uma pose."""

    def __init__(self, p: Pose):
        self.H = (32 + p.x, 40 + p.y)
        self.u = (math.sin(math.radians(p.incl)), -math.cos(math.radians(p.incl)))   # para cima no tronco
        self.f = (math.cos(math.radians(p.incl)), math.sin(math.radians(p.incl)))    # para frente no tronco
        self.N = soma(self.H, self.u, 13)
        self.S = soma(self.N, self.u, -2)
        self.C = soma(soma(self.N, self.u, 6), self.f, 1)  # centro da cabeca
        self.maos: dict[str, tuple] = {}


def desenhar(p: Pose, e: Estilo) -> Img:
    img = Img(Q, Q)
    g = Geo(p)
    rim = e.rim

    def perna(frente: bool):
        ang, dob = p.pf if frente else p.pt
        quad = soma(g.H, g.f, 1.5 if frente else -1.5)
        joe = soma(quad, dirv(ang), 10)
        tor = soma(joe, dirv(ang - dob), 10)
        esc = 0 if frente else 1
        img.capsula(*quad, *joe, 3.4, 2.8, e.calca, rim=rim, escuro=esc)
        img.capsula(*joe, *tor, 2.8, 2.3, e.calca, rim=rim, escuro=esc)
        cano = soma(tor, dirv(ang - dob), -3.5)
        img.capsula(*cano, *tor, 2.7, 2.6, e.bota, rim=rim, escuro=esc)
        pe = soma(tor, dirv(ang - dob + 90), 4.5)
        img.capsula(*tor, *pe, 2.6, 2.0, e.bota, rim=rim, escuro=esc)

    def braco(frente: bool):
        sh, el = p.bf if frente else p.bt
        ombro = soma(g.S, g.f, 1.5 if frente else -2.5)
        cot = soma(ombro, dirv(sh), 7.5)
        pulso = soma(cot, dirv(sh + el), 7)
        mao = soma(pulso, dirv(sh + el), 1.4)
        esc = 0 if frente else 1
        g.maos["frente" if frente else "tras"] = (mao, sh + el, cot, pulso)
        img.capsula(*ombro, *cot, 2.9, 2.5, e.jaqueta, rim=rim, escuro=esc)
        if frente and p.arma == "canhao":
            return  # o antebraco vira canhao (desenhado na arma)
        img.capsula(*cot, *pulso, 2.5, 2.1, e.jaqueta, rim=rim, escuro=esc)
        img.elipse(*mao, 2.1, 2.1, e.luva, rim=rim, escuro=esc)

    braco(False)
    perna(False)
    e.cachecol_tras(img, g, p)
    # tronco + barra da jaqueta
    img.capsula(*soma(g.H, g.u, -3.5), *soma(g.H, g.u, 2), e.largura_quadril + 0.8, e.largura_quadril + 0.6, e.jaqueta, rim=rim, escuro=1)
    img.capsula(*g.H, *g.N, e.largura_quadril, e.largura_peito, e.jaqueta, rim=rim)
    e.roupa(img, g, p)
    perna(True)
    img.capsula(*g.N, *soma(g.N, g.u, 3), 2.2, 2.2, e.pele, rim=rim, escuro=1)  # pescoco
    e.cabeca(img, g, p)
    braco(True)
    e.arma(img, g, p)
    luz_de_borda(img)
    img.contorno(K)
    e.brilhos(img, g, p)
    return img


def luz_de_borda(img: Img, cor=NEON_BORDA, forca=0.45) -> None:
    """Neon da cidade batendo por tras: clareia so os pixels da silhueta voltados para tras/cima."""
    marcar = []
    for y in range(img.h):
        for x in range(img.w):
            if not img.cheio(x, y):
                continue
            atras = not img.cheio(x - 1, y)
            cima = not img.cheio(x, y - 1) and not img.cheio(x - 1, y - 1)
            if atras or cima:
                marcar.append((x, y, forca if atras else forca * 0.6))
    for x, y, f in marcar:
        c = img.px[y][x]
        img.px[y][x] = tuple(round(c[i] + (cor[i] - c[i]) * f) for i in range(3))


# ======================================================================== MARCO

class EstiloMarco(Estilo):
    def cachecol_tras(self, img, g, p):
        pontos = [soma(soma(g.N, g.f, -3), g.u, 0.5)]
        ang = math.radians(p.vento_dir)
        for i in range(1, 8):
            onda = math.sin(p.fase * 2 * math.pi * 2 + i * 0.9) * (0.4 + p.vento) * i * 0.35
            forca = 0.45 + 0.55 * min(1.0, p.vento)
            base = (-math.cos(ang) * 3.0 * forca, math.sin(ang) * 3.0 * forca + 2.4 * (1 - min(1.0, p.vento)))
            nx, ny = -base[1], base[0]
            n = math.hypot(nx, ny) or 1
            pontos.append((pontos[-1][0] + base[0] + nx / n * onda * 0.5, pontos[-1][1] + base[1] + ny / n * onda * 0.5))
        for i in range(len(pontos) - 1):
            r0 = 2.2 - i * 0.18
            img.capsula(*pontos[i], *pontos[i + 1], r0, r0 - 0.18, CACHECOL, escuro=1)

    def roupa(self, img, g, p):
        # ziper
        for i in range(2, 12):
            x, y = soma(soma(g.H, g.u, i), g.f, 2.6)
            img.set(x, y, JAQUETA_MARCO[0])
        # faixa refletiva (catador)
        meio = soma(g.H, g.u, 6)
        a, b = soma(meio, g.f, -4.5), soma(meio, g.f, 4.5)
        img.capsula(*a, *b, 0.75, 0.75, [(80, 110, 120), (130, 170, 180), (180, 220, 228), (220, 250, 255)], borda=False)
        # bolso
        x, y = soma(soma(g.H, g.u, 2.5), g.f, 0.5)
        img.rect(x, y, 3, 1, JAQUETA_MARCO[0])
        # capuz caido nas costas
        cap = soma(soma(g.N, g.f, -3.2), g.u, -1.5)
        img.elipse(*cap, 3.4, 2.6, JAQUETA_MARCO, escuro=1)

    def cabeca(self, img, g, p):
        C = g.C
        img.elipse(*soma(C, (-1.2, 0.8)), 1.3, 1.7, PELE, escuro=1)  # orelha
        img.elipse(*C, 4.6, 5.2, PELE)
        cx, cy = C
        # rosto
        img.set(cx + 2.4, cy - 0.6, K)
        img.set(cx + 2.4, cy + 0.4, K)
        img.set(cx + 1.4, cy - 1.8, CABELO[1])
        img.set(cx + 2.4, cy - 2.0, CABELO[1])
        img.set(cx + 3.4, cy - 1.8, CABELO[1])
        img.set(cx + 4.6, cy + 0.6, PELE[1])
        img.set(cx + 2.4, cy + 2.6, PELE[0])
        img.set(cx + 3.4, cy + 2.6, PELE[1])
        # cabelo bagunçado, com uma mecha voando ao vento
        v = p.vento * 1.5
        cabelo = [
            (cx - 5.2, cy + 2.5), (cx - 6.4 - v, cy - 1), (cx - 5.6 - v, cy - 4.5), (cx - 3.2, cy - 7.2),
            (cx - 0.5, cy - 6.4), (cx + 1.5, cy - 7.8), (cx + 4.2, cy - 6.6), (cx + 5.8, cy - 3.6),
            (cx + 4.6, cy - 3.8), (cx + 3.4, cy - 2.6), (cx + 1.8, cy - 3.6), (cx - 0.4, cy - 2.4),
            (cx - 1.6, cy - 0.8), (cx - 2.2, cy + 1.6), (cx - 3.4, cy + 3.6),
        ]
        img.poligono_sombreado(cabelo, CABELO, cx, cy - 1, 6, 6.5)
        for x, y in ((cx - 2, cy - 5.6), (cx - 1, cy - 5.6), (cx + 2, cy - 6.2), (cx + 3, cy - 5.6)):
            img.set(x, y, CABELO[3])
        # cachecol enrolado no pescoco
        img.capsula(*soma(g.N, g.f, -3), *soma(g.N, g.f, 3.2), 2.4, 2.2, CACHECOL)

    def arma(self, img, g, p):
        mao, ang, cot, pulso = g.maos["frente"]
        if p.arma == "canhao":
            boca = soma(pulso, dirv(ang), 4)
            img.capsula(*cot, *boca, 3.0, 3.6, CANHAO)
            img.capsula(*soma(boca, dirv(ang), -1), *boca, 3.4, 3.4, METAL)

    def brilhos(self, img, g, p):
        # A ESCAMA na nuca + circuitos subindo o pescoco
        ch = soma(soma(g.N, g.f, -3.6), g.u, 2.6)
        pulso = max(0.0, min(1.0, p.brilho))
        img.brilho(*ch, 5, CIANO, 150 * pulso)
        img.rect(ch[0] - 1, ch[1] - 1, 2, 2, CIANO if pulso > 0.15 else (40, 90, 100))
        img.set(ch[0] - 1, ch[1] - 1, BRANCO if pulso > 0.5 else CIANO)
        for i in range(1, 4):
            x, y = soma(ch, g.u, i + 1)
            img.set(x - 0.5, y, alfa(CIANO, 170 * pulso))
        mao, ang, cot, pulso_p = g.maos["frente"]
        a = p.arma_ang if p.arma_ang is not None else ang
        if p.arma in ("lamina", "lamina_curta"):
            comp = 17 if p.arma == "lamina" else 9
            fim = soma(mao, dirv(a), comp)
            img.capsula(*mao, *fim, 1.8, 1.2, [alfa(CIANO, 120)] * 4, borda=False)
            img.linha(*mao, *fim, BRANCO)
            img.brilho(*mao, 4, CIANO, 160)
        elif p.arma == "canhao":
            boca = soma(pulso_p, dirv(ang), 5)
            img.brilho(*boca, 5 if not p.clarao else 9, AMARELO, 170)
            img.disco(*boca, 1.3, AMARELO)
            if p.clarao:
                img.disco(*soma(boca, dirv(ang), 3), 3, (255, 240, 200))


MARCO = EstiloMarco()


def anims_marco() -> dict[str, tuple[list[Pose], int, int]]:
    """nome -> (poses, fps, repetir: -1 loop / 0 uma vez)"""
    A: dict[str, tuple[list[Pose], int, int]] = {}
    TAU = 2 * math.pi

    A["parado"] = ([Pose(
        y=1 if math.sin(TAU * i / 8) < -0.3 else 0, incl=4 + math.sin(TAU * i / 8),
        bf=(10 + 3 * math.sin(TAU * i / 8), 22), bt=(-12 - 3 * math.sin(TAU * i / 8), 20),
        pf=(9, 8), pt=(-9, 8), vento=0.3, fase=i / 8, brilho=0.55 + 0.45 * (0.5 + 0.5 * math.sin(TAU * i / 8)),
    ) for i in range(8)], 8, -1)

    corr = []
    for i in range(8):
        a = TAU * i / 8
        corr.append(Pose(
            y=round(1.6 * abs(math.sin(a))) - 1, incl=15,
            pf=(46 * math.sin(a) - 2, 12 + 64 * max(0, math.cos(a))),
            pt=(46 * math.sin(a + math.pi) - 2, 12 + 64 * max(0, math.cos(a + math.pi))),
            bf=(-52 * math.sin(a) + 5, 80), bt=(52 * math.sin(a) - 5, 80),
            vento=1.0, vento_dir=-4, fase=i / 8,
        ))
    A["correr"] = (corr, 16, -1)

    agach = Pose(y=5, incl=18, pf=(50, 92), pt=(22, 80), bf=(-35, 50), bt=(-60, 35), vento=0.4)
    A["pulo"] = ([agach, Pose(y=-1, incl=6, pf=(8, 8), pt=(-14, 14), bf=(150, 15), bt=(-95, 20), vento=0.7, vento_dir=35)], 20, 0)
    A["subindo"] = ([Pose(y=-2, incl=6, pf=(62, 88), pt=(24, 72), bf=(150 + k * 6, -5), bt=(-80, 30),
                          vento=0.8, vento_dir=40, fase=k / 2) for k in range(2)], 10, -1)
    A["apice"] = ([Pose(incl=8, pf=(46, 62), pt=(12, 52), bf=(112, 12), bt=(-104, 10), vento=0.5, vento_dir=5)], 1, 0)
    A["caindo"] = ([Pose(incl=6, pf=(24, 22), pt=(-12, 40), bf=(122 + k * 6, -12), bt=(-124, -8),
                         vento=0.9, vento_dir=-55, fase=k / 2) for k in range(2)], 10, -1)
    A["aterrissar"] = ([
        Pose(y=6, incl=24, pf=(58, 100), pt=(26, 90), bf=(40, 30), bt=(-10, 40), vento=0.5, vento_dir=20),
        Pose(y=3, incl=14, pf=(30, 50), pt=(10, 40), bf=(25, 25), bt=(-15, 25), vento=0.4),
        Pose(y=1, incl=7, pf=(14, 14), pt=(-6, 12), bf=(12, 22), bt=(-12, 20), vento=0.3),
    ], 18, 0)

    lunge = dict(pf=(36, 22), pt=(-32, 16))
    A["ataque_frente"] = ([
        Pose(incl=-4, bf=(-145, -20), bt=(-30, 30), pf=(20, 12), pt=(-18, 10), vento=0.6),
        Pose(y=1, incl=20, bf=(95, -5), bt=(-60, 20), arma="lamina", arma_ang=125, vento=0.9, **lunge),
        Pose(y=1, incl=24, bf=(62, -5), bt=(-70, 20), arma="lamina", arma_ang=70, vento=1.0, **lunge),
        Pose(y=1, incl=18, bf=(34, 10), bt=(-55, 25), arma="lamina_curta", arma_ang=40, vento=0.8, **lunge),
        Pose(incl=10, bf=(20, 20), bt=(-30, 25), pf=(22, 14), pt=(-20, 12), vento=0.6),
    ], 30, 0)
    A["ataque_cima"] = ([
        Pose(y=3, incl=10, bf=(10, 35), bt=(-30, 30), pf=(30, 40), pt=(-10, 35), vento=0.5),
        Pose(y=-1, incl=-6, bf=(150, 0), bt=(-70, 20), arma="lamina", arma_ang=165, pf=(14, 20), pt=(-12, 14), vento=0.8, vento_dir=30),
        Pose(y=-2, incl=-12, bf=(182, -5), bt=(-90, 20), arma="lamina", arma_ang=200, pf=(10, 20), pt=(-14, 18), vento=0.9, vento_dir=40),
        Pose(y=-1, incl=-8, bf=(200, 10), bt=(-80, 20), arma="lamina_curta", arma_ang=215, pf=(10, 14), pt=(-10, 14), vento=0.6),
        Pose(incl=2, bf=(120, 30), bt=(-40, 25), pf=(12, 10), pt=(-10, 10), vento=0.5),
    ], 30, 0)
    A["ataque_baixo"] = ([
        Pose(y=-1, incl=2, bf=(172, 10), bt=(-40, 20), pf=(16, 12), pt=(-14, 12), vento=0.5),
        Pose(y=2, incl=26, bf=(70, 0), bt=(-80, 20), arma="lamina", arma_ang=45, pf=(44, 50), pt=(-24, 30), vento=0.9),
        Pose(y=3, incl=32, bf=(30, 0), bt=(-90, 20), arma="lamina", arma_ang=15, pf=(48, 56), pt=(-26, 34), vento=1.0),
        Pose(y=3, incl=28, bf=(12, 10), bt=(-70, 25), arma="lamina_curta", arma_ang=-5, pf=(46, 52), pt=(-24, 30), vento=0.7),
        Pose(y=1, incl=14, bf=(18, 20), bt=(-30, 25), pf=(24, 22), pt=(-14, 16), vento=0.5),
    ], 30, 0)
    A["canhao"] = ([
        Pose(incl=2, bf=(75, 12), bt=(-25, 30), pf=(18, 10), pt=(-16, 10), arma="canhao", vento=0.4),
        Pose(incl=-7, bf=(92, 0), bt=(-35, 30), pf=(20, 10), pt=(-20, 14), arma="canhao", clarao=True, vento=0.7),
        Pose(incl=-5, bf=(100, 0), bt=(-30, 30), pf=(20, 10), pt=(-20, 14), arma="canhao", vento=0.6),
        Pose(incl=0, bf=(86, 6), bt=(-25, 30), pf=(18, 10), pt=(-16, 10), arma="canhao", vento=0.4),
    ], 24, 0)
    A["morte"] = (poses_morte(marco=True), 14, 0)
    return A


def poses_morte(marco=False) -> list[Pose]:
    """Atingido -> cai de costas -> bate no chao -> fica caido."""
    v = dict(vento=0.6) if marco else {}
    return [
        Pose(incl=-24, bf=(-150, 40), bt=(-120, 20), pf=(22, 30), pt=(-8, 22), **v),
        Pose(y=3, incl=-48, bf=(-170, 20), bt=(-140, 20), pf=(58, 70), pt=(36, 66), vento_dir=-40, **v),
        Pose(y=9, incl=-72, bf=(-160, 30), bt=(-150, 10), pf=(84, 42), pt=(66, 40), vento_dir=-60, **v),
        Pose(y=16, incl=-90, bf=(-175, 20), bt=(-160, 10), pf=(96, 12), pt=(84, 12), **v),
        Pose(y=14, incl=-86, bf=(-160, 40), bt=(-150, 20), pf=(92, 16), pt=(80, 16), **v),
        Pose(y=16, incl=-90, bf=(-178, 15), bt=(-165, 5), pf=(96, 10), pt=(84, 12), brilho=0.6, **v),
        Pose(y=16, incl=-90, bf=(-180, 10), bt=(-168, 5), pf=(96, 8), pt=(86, 10), brilho=0.3, **v),
        Pose(y=16, incl=-90, bf=(-180, 10), bt=(-168, 5), pf=(96, 8), pt=(86, 10), brilho=0.0, **v),
    ]


# ======================================================================== CATADOR

class EstiloCatador(Estilo):
    largura_quadril = 5.4
    largura_peito = 7.0
    calca = TRAPO2
    jaqueta = TRAPO
    luva = rampa((26, 20, 18), (52, 40, 34), (80, 62, 50), (110, 88, 70))
    pele = PELE_ESCURA

    def roupa(self, img, g, p):
        for (u, f, cor) in ((4, -2, TRAPO2[1]), (8, 1.5, (96, 40, 40)), (2, 2.5, TRAPO2[2])):  # remendos
            x, y = soma(soma(g.H, g.u, u), g.f, f)
            img.rect(x, y, 3, 2, cor)
        for i in range(1, 12, 2):  # costura
            x, y = soma(soma(g.H, g.u, i), g.f, -0.5)
            img.set(x, y, TRAPO[0])
        # cinto com ferramentas
        x, y = soma(g.H, g.u, 0.5)
        img.capsula(*soma((x, y), g.f, -5), *soma((x, y), g.f, 5), 0.9, 0.9, rampa((20, 14, 12), (40, 28, 22), (64, 46, 34), (90, 66, 48)), borda=False)

    def cabeca(self, img, g, p):
        cx, cy = g.C
        img.elipse(cx, cy, 4.8, 5.2, PELE_ESCURA)
        # capuz de trapo
        capuz = [(cx - 6, cy + 4), (cx - 6.6, cy - 2), (cx - 4, cy - 6.6), (cx + 1, cy - 7.2), (cx + 4.6, cy - 5),
                 (cx + 5.6, cy - 2.2), (cx + 3, cy - 3.4), (cx - 1, cy - 2.6), (cx - 2.4, cy + 2), (cx - 3.4, cy + 5)]
        img.poligono_sombreado(capuz, CAPUZ, cx - 1, cy - 1, 6.5, 6.5)
        # mascara respiratoria + filtro
        img.elipse(cx + 2.6, cy + 2.2, 2.8, 2.3, MASCARA)
        img.elipse(cx + 3.6, cy + 3.8, 1.7, 1.7, METAL)
        img.set(cx + 3.6, cy + 3.8, K)
        # oculos (lentes desenhadas nos brilhos)
        img.rect(cx + 0.6, cy - 1.6, 5, 2.4, (24, 10, 20))

    def arma(self, img, g, p):
        mao, ang, cot, pulso = g.maos["frente"]
        a = p.arma_ang if p.arma_ang is not None else ang
        if p.arma == "cano":
            fim = soma(mao, dirv(a), 15)
            img.capsula(*soma(mao, dirv(a), -3), *fim, 1.4, 1.4, METAL)
            img.capsula(*soma(fim, dirv(a), -2), *fim, 2.2, 2.2, METAL)  # joelho do cano
            img.elipse(*mao, 2.2, 2.2, self.luva)

    def brilhos(self, img, g, p):
        cx, cy = g.C
        b = max(0.0, min(1.0, p.brilho))
        for x in (cx + 1.2, cx + 3.8):
            img.rect(x, cy - 1.4, 2, 2, ROSA if b > 0.2 else (90, 30, 50))
            img.set(x, cy - 1.4, (255, 190, 210) if b > 0.5 else ROSA)
            img.brilho(x + 1, cy - 0.4, 4, ROSA, 120 * b)


CATADOR = EstiloCatador()


def anims_catador():
    TAU = 2 * math.pi
    A = {}
    A["parado"] = ([Pose(y=1 if i in (2, 3, 4) else 0, incl=20 + math.sin(TAU * i / 6) * 2, bf=(42, 42), bt=(-8, 22),
                         pf=(10, 10), pt=(-8, 10), arma="cano", brilho=0.7 + 0.3 * math.sin(TAU * i / 6)) for i in range(6)], 6, -1)
    andar = []
    for i in range(8):
        a = TAU * i / 8
        andar.append(Pose(y=round(abs(math.sin(a))), incl=22, pf=(28 * math.sin(a), 10 + 40 * max(0, math.cos(a))),
                          pt=(28 * math.sin(a + math.pi), 10 + 40 * max(0, math.cos(a + math.pi))),
                          bf=(40 + 6 * math.sin(a), 40), bt=(24 * math.sin(a), 26), arma="cano"))
    A["andar"] = (andar, 10, -1)
    correr = []
    for i in range(8):
        a = TAU * i / 8
        correr.append(Pose(y=round(1.6 * abs(math.sin(a))) - 1, incl=30, pf=(44 * math.sin(a), 12 + 60 * max(0, math.cos(a))),
                           pt=(44 * math.sin(a + math.pi), 12 + 60 * max(0, math.cos(a + math.pi))),
                           bf=(75, 30), bt=(-50 * math.sin(a), 70), arma="cano"))
    A["correr"] = (correr, 16, -1)
    ini = Pose(incl=20, bf=(42, 42), bt=(-8, 22), pf=(14, 10), pt=(-10, 10), arma="cano")
    alto = Pose(y=2, incl=-10, bf=(-140, 18), bt=(-40, 30), pf=(26, 24), pt=(-18, 18), arma="cano", brilho=1.4)
    A["preparar"] = ([lerp_pose(ini, alto, t) for t in (0.3, 0.6, 0.85, 1.0)], 14, 0)
    A["golpe"] = ([
        Pose(y=1, incl=26, bf=(115, -10), bt=(-60, 30), pf=(40, 26), pt=(-30, 20), arma="cano"),
        Pose(y=2, incl=34, bf=(62, 0), bt=(-70, 30), pf=(44, 30), pt=(-34, 22), arma="cano"),
        Pose(y=2, incl=32, bf=(36, 12), bt=(-60, 30), pf=(42, 28), pt=(-32, 20), arma="cano"),
        Pose(y=1, incl=26, bf=(38, 30), bt=(-30, 25), pf=(26, 18), pt=(-20, 14), arma="cano"),
    ], 22, 0)
    A["morte"] = ([replace(q, brilho=max(0, 1 - i * 0.15)) for i, q in enumerate(poses_morte())], 14, 0)
    return A


# ======================================================================== PISTOLEIRO

class EstiloPistoleiro(Estilo):
    largura_quadril = 4.0
    largura_peito = 5.0
    calca = CALCA_PIST
    jaqueta = JAQUETA_PIST
    luva = PELE

    def roupa(self, img, g, p):
        for i in range(2, 12):  # ziper
            x, y = soma(soma(g.H, g.u, i), g.f, 2.2)
            img.set(x, y, JAQUETA_PIST[0])
        x, y = soma(g.H, g.u, 0.5)  # barra elastica
        img.capsula(*soma((x, y), g.f, -4.5), *soma((x, y), g.f, 4.5), 1.0, 1.0, rampa((60, 20, 14), (100, 40, 20), (130, 60, 30), (160, 90, 50)), borda=False)
        img.capsula(*soma(g.N, g.f, -3.5), *soma(g.N, g.f, 3.0), 2.6, 2.4, GOLA)  # gola

    def cabeca(self, img, g, p):
        cx, cy = g.C
        img.elipse(*soma(g.C, (-1.2, 0.8)), 1.3, 1.7, PELE, escuro=1)
        img.elipse(cx, cy, 4.4, 5.0, PELE)
        img.set(cx + 2.4, cy - 0.4, K)
        img.set(cx + 2.4, cy + 0.6, K)
        img.set(cx + 4.4, cy + 0.8, PELE[1])
        img.rect(cx + 1.4, cy + 2.4, 3, 1, PELE[0])
        img.rect(cx - 4.4, cy - 0.5, 2, 4, CABELO[1])  # costeleta
        bone = [(cx - 5, cy - 1), (cx - 4.6, cy - 4.6), (cx - 1.5, cy - 6.6), (cx + 2.5, cy - 6.4), (cx + 4.6, cy - 3.6),
                (cx + 8.2, cy - 2.8), (cx + 8.0, cy - 1.6), (cx + 4, cy - 1.8), (cx - 1, cy - 1.6)]
        img.poligono_sombreado(bone, BONE, cx, cy - 3, 6, 4.5)
        img.set(cx + 0.5, cy - 5.2, (255, 140, 66))
        for i in range(-2, 3):  # corrente dourada
            x, y = soma(soma(g.N, g.f, i * 1.1), g.u, -1.5 - abs(i) * 0.4)
            img.set(x, y, OURO)

    def arma(self, img, g, p):
        mao, ang, cot, pulso = g.maos["frente"]
        if p.arma in ("pistola", "tiro"):
            fim = soma(mao, dirv(ang), 6.5)
            img.capsula(*soma(mao, dirv(ang), 0.5), *fim, 1.5, 1.4, ARMA)
            img.capsula(*mao, *soma(mao, dirv(ang - 90), 2.2), 1.1, 1.0, ARMA)  # cabo
            img.elipse(*mao, 2.0, 2.0, PELE)

    def brilhos(self, img, g, p):
        mao, ang, cot, pulso = g.maos["frente"]
        if p.clarao:
            boca = soma(mao, dirv(ang), 9)
            img.brilho(*boca, 7, AMARELO, 200)
            img.disco(*boca, 2.2, (255, 244, 210))
            for k in (-30, 0, 30):
                img.linha(*boca, *soma(boca, dirv(ang + k), 5), AMARELO)


PISTOLEIRO = EstiloPistoleiro()


def anims_pistoleiro():
    TAU = 2 * math.pi
    A = {}
    A["parado"] = ([Pose(x=0.6 * math.sin(TAU * i / 6), y=1 if i in (2, 3) else 0, incl=2, bf=(12, 26), bt=(-10, 16),
                         pf=(10, 8), pt=(-10, 8), arma="pistola") for i in range(6)], 6, -1)
    baixo = Pose(incl=2, bf=(12, 26), bt=(-10, 16), pf=(12, 8), pt=(-12, 8), arma="pistola")
    mira = Pose(incl=-3, bf=(90, 0), bt=(-20, 30), pf=(16, 8), pt=(-16, 10), arma="pistola")
    A["mirar"] = ([lerp_pose(baixo, mira, t) for t in (0.35, 0.7, 1.0)], 16, 0)
    A["atirar"] = ([
        replace(mira, incl=-8, bf=(100, -4), clarao=True, arma="tiro"),
        replace(mira, incl=-6, bf=(96, -2)),
        replace(mira, incl=-4, bf=(92, 0)),
    ], 20, 0)
    A["morte"] = (poses_morte(), 14, 0)
    return A


PERSONAGENS = {
    "marco": (MARCO, anims_marco),
    "catador": (CATADOR, anims_catador),
    "pistoleiro": (PISTOLEIRO, anims_pistoleiro),
}
