"""Personagens de DOWNGRADE: esqueleto (rig) + poses-chave + animacoes.

Quadros de 64x64, personagem olhando para a DIREITA, pes na base (y=63).
Angulos dos membros em graus: 0 = para baixo, 90 = para frente, 180 = para cima, -90 = para tras.

Principios de animacao usados (para movimento fluido e com peso):
- poses-chave (contato, recuo, passagem, impulso) interpoladas com suavizacao (slow-in / slow-out)
- pes plantados: a altura do corpo e calculada para o ponto mais baixo tocar o chao
- antecipacao antes do golpe, rastro (smear) no golpe, continuacao e acomodacao depois
- movimento secundario: torcao de ombros, cabeca com atraso, barra da jaqueta, cachecol, piscada
"""
from __future__ import annotations

import math
from dataclasses import dataclass, fields, replace

from pixel import Img, alfa

Q = 64  # tamanho do quadro
CHAO = 63  # linha do contorno dos pes
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
    y: float = 0             # so vale quando apoiado=False (no ar)
    incl: float = 0          # inclinacao do tronco (+ = para frente)
    bf: tuple = (15, 15)     # braco da frente (ombro, cotovelo)
    bt: tuple = (-15, 15)    # braco de tras
    pf: tuple = (8, 6)       # perna da frente (quadril, joelho)
    pt: tuple = (-8, 6)      # perna de tras
    torcao: float = 0        # ombros girando contra o quadril (px)
    cab: tuple = (0, 0)      # deslocamento da cabeca (atraso / peso)
    barra: float = 0         # barra da jaqueta abrindo para tras (px)
    voo: float = 0           # sobe o corpo depois de plantar os pes (fase de voo da corrida)
    apoiado: bool = True     # True = pes plantados no chao automaticamente
    vento: float = 0.5       # forca do vento no cachecol
    vento_dir: float = 0     # direcao do cachecol: 0 = para tras, + = para baixo, - = para cima
    fase: float = 0
    piscar: bool = False
    arma: str = ""
    arma_ang: float | None = None
    rastro: tuple | None = None  # (angulo_inicial, angulo_final) do smear da arma
    brilho: float = 1.0      # pulso da Escama / olhos neon
    clarao: bool = False     # clarao de tiro


def lerp_pose(a: Pose, b: Pose, t: float) -> Pose:
    kw = {}
    for f in fields(Pose):
        va, vb = getattr(a, f.name), getattr(b, f.name)
        if isinstance(va, tuple) and isinstance(vb, tuple):
            kw[f.name] = tuple(x + (y - x) * t for x, y in zip(va, vb))
        elif isinstance(va, (int, float)) and isinstance(vb, (int, float)) and not isinstance(va, bool) \
                and va is not None and vb is not None:
            kw[f.name] = va + (vb - va) * t
        else:
            kw[f.name] = vb if t >= 0.5 else va
    return Pose(**kw)


def suave(t: float) -> float:
    return t * t * (3 - 2 * t)


def chaves(keys: list[tuple[float, Pose]], n: int, loop: bool = False, fase_ciclo: bool = True) -> list[Pose]:
    """Gera n quadros interpolando poses-chave [(t, pose)] com slow-in/slow-out."""
    ks = list(keys) + ([(1.0, keys[0][1])] if loop else [])
    quadros = []
    for i in range(n):
        t = i / n if loop else (i / (n - 1) if n > 1 else 0)
        for j in range(len(ks) - 1):
            (t0, a), (t1, b) = ks[j], ks[j + 1]
            if t0 <= t <= t1:
                p = lerp_pose(a, b, suave((t - t0) / max(1e-6, t1 - t0)))
                break
        else:
            p = ks[-1][1]
        quadros.append(replace(p, fase=i / n) if fase_ciclo else p)
    return quadros


def espelhar_pernas(p: Pose, bracos: bool = True) -> Pose:
    """Segunda metade de um ciclo: a perna (e o braco) da frente faz o papel da de tras."""
    kw = dict(pf=p.pt, pt=p.pf, torcao=-p.torcao)
    if bracos:
        kw.update(bf=p.bt, bt=p.bf)
    return replace(p, **kw)


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
        self.C = soma(soma(soma(self.N, self.u, 6), self.f, 1), p.cab)  # centro da cabeca
        self.maos: dict[str, tuple] = {}


def desenhar(p: Pose, e: Estilo) -> Img:
    """Desenha a pose. Se apoiado, primeiro mede o ponto mais baixo e planta no chao."""
    if p.apoiado:
        teste = _render(replace(p, y=0), e, brilhos=False)
        baixo = max((y for y in range(Q) for x in range(Q) if teste.px[y][x] is not None), default=CHAO)
        p = replace(p, y=CHAO - baixo - p.voo)
    return _render(p, e, brilhos=True)


def _render(p: Pose, e: Estilo, brilhos: bool) -> Img:
    img = Img(Q, Q)
    g = Geo(p)

    def perna(frente: bool):
        ang, dob = p.pf if frente else p.pt
        quad = soma(g.H, g.f, (1.5 - p.torcao * 0.3) if frente else (-1.5 + p.torcao * 0.3))
        joe = soma(quad, dirv(ang), 10)
        tor = soma(joe, dirv(ang - dob), 10)
        esc = 0 if frente else 1
        img.capsula(*quad, *joe, 3.4, 2.8, e.calca, escuro=esc)
        img.capsula(*joe, *tor, 2.8, 2.3, e.calca, escuro=esc)
        cano = soma(tor, dirv(ang - dob), -3.5)
        img.capsula(*cano, *tor, 2.7, 2.6, e.bota, escuro=esc)
        pe = soma(tor, dirv(ang - dob + 90), 4.5)
        img.capsula(*tor, *pe, 2.6, 2.0, e.bota, escuro=esc)

    def braco(frente: bool):
        sh, el = p.bf if frente else p.bt
        ombro = soma(g.S, g.f, (1.5 + p.torcao) if frente else (-2.5 - p.torcao * 0.6))
        cot = soma(ombro, dirv(sh), 7.5)
        pulso = soma(cot, dirv(sh + el), 7)
        mao = soma(pulso, dirv(sh + el), 1.4)
        esc = 0 if frente else 1
        g.maos["frente" if frente else "tras"] = (mao, sh + el, cot, pulso)
        img.capsula(*ombro, *cot, 2.9, 2.5, e.jaqueta, escuro=esc)
        if frente and p.arma == "canhao":
            return  # o antebraco vira canhao (desenhado na arma)
        img.capsula(*cot, *pulso, 2.5, 2.1, e.jaqueta, escuro=esc)
        img.elipse(*mao, 2.1, 2.1, e.luva, escuro=esc)

    braco(False)
    perna(False)
    e.cachecol_tras(img, g, p)
    # barra da jaqueta (abre para tras com o movimento) + tronco
    barra_a = soma(soma(g.H, g.u, -3.5), g.f, -p.barra)
    barra_b = soma(g.H, g.u, 2)
    img.capsula(*barra_a, *barra_b, e.largura_quadril + 0.8, e.largura_quadril + 0.6, e.jaqueta, escuro=1)
    img.capsula(*g.H, *g.N, e.largura_quadril, e.largura_peito, e.jaqueta)
    e.roupa(img, g, p)
    perna(True)
    img.capsula(*g.N, *soma(g.N, g.u, 3), 2.2, 2.2, e.pele, escuro=1)  # pescoco
    e.cabeca(img, g, p)
    braco(True)
    e.arma(img, g, p)
    luz_de_borda(img)
    img.contorno(K)
    if brilhos:
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


def rastro(img: Img, pivo, a0: float, a1: float, comp: float, cor, forca=1.0) -> None:
    """Smear: leque semitransparente varrido pela arma entre dois angulos."""
    passos = max(2, int(abs(a1 - a0) / 6))
    for i in range(passos):
        t = i / (passos - 1)
        a = a0 + (a1 - a0) * t
        fim = soma(pivo, dirv(a), comp)
        img.linha(*soma(pivo, dirv(a), comp * 0.45), *fim, alfa(cor, (25 + 150 * t * t) * forca))


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
        for i in range(2, 12):  # ziper
            x, y = soma(soma(g.H, g.u, i), g.f, 2.6)
            img.set(x, y, JAQUETA_MARCO[0])
        meio = soma(g.H, g.u, 6)  # faixa refletiva (catador)
        a, b = soma(meio, g.f, -4.5), soma(meio, g.f, 4.5)
        img.capsula(*a, *b, 0.75, 0.75, [(80, 110, 120), (130, 170, 180), (180, 220, 228), (220, 250, 255)], borda=False)
        x, y = soma(soma(g.H, g.u, 2.5), g.f, 0.5)  # bolso
        img.rect(x, y, 3, 1, JAQUETA_MARCO[0])
        cap = soma(soma(g.N, g.f, -3.2 - p.barra * 0.2), g.u, -1.5)  # capuz caido balancando
        img.elipse(*cap, 3.4, 2.6, JAQUETA_MARCO, escuro=1)

    def cabeca(self, img, g, p):
        C = g.C
        img.elipse(*soma(C, (-1.2, 0.8)), 1.3, 1.7, PELE, escuro=1)  # orelha
        img.elipse(*C, 4.6, 5.2, PELE)
        cx, cy = C
        if p.piscar:
            img.set(cx + 2.4, cy + 0.4, PELE[0])
            img.set(cx + 3.4, cy + 0.4, PELE[0])
        else:
            img.set(cx + 2.4, cy - 0.6, K)
            img.set(cx + 2.4, cy + 0.4, K)
        img.set(cx + 1.4, cy - 1.8, CABELO[1])
        img.set(cx + 2.4, cy - 2.0, CABELO[1])
        img.set(cx + 3.4, cy - 1.8, CABELO[1])
        img.set(cx + 4.6, cy + 0.6, PELE[1])
        img.set(cx + 2.4, cy + 2.6, PELE[0])
        img.set(cx + 3.4, cy + 2.6, PELE[1])
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
        img.capsula(*soma(g.N, g.f, -3), *soma(g.N, g.f, 3.2), 2.4, 2.2, CACHECOL)

    def arma(self, img, g, p):
        mao, ang, cot, pulso = g.maos["frente"]
        if p.arma == "canhao":
            boca = soma(pulso, dirv(ang), 4)
            img.capsula(*cot, *boca, 3.0, 3.6, CANHAO)
            img.capsula(*soma(boca, dirv(ang), -1), *boca, 3.4, 3.4, METAL)

    def brilhos(self, img, g, p):
        ch = soma(soma(g.N, g.f, -3.6), g.u, 2.6)  # a ESCAMA na nuca
        pulso = max(0.0, min(1.0, p.brilho))
        img.brilho(*ch, 5, CIANO, 150 * pulso)
        img.rect(ch[0] - 1, ch[1] - 1, 2, 2, CIANO if pulso > 0.15 else (40, 90, 100))
        img.set(ch[0] - 1, ch[1] - 1, BRANCO if pulso > 0.5 else CIANO)
        for i in range(1, 4):
            x, y = soma(ch, g.u, i + 1)
            img.set(x - 0.5, y, alfa(CIANO, 170 * pulso))
        mao, ang, cot, pulso_p = g.maos["frente"]
        a = p.arma_ang if p.arma_ang is not None else ang
        if p.rastro:
            rastro(img, mao, p.rastro[0], p.rastro[1], 19, CIANO)
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

# ---- poses de referencia do Marco
NEUTRO = Pose(incl=4, bf=(8, 20), bt=(-10, 18), pf=(8, 6), pt=(-8, 6), vento=0.3)

# Ciclo de corrida: 4 poses-chave por passada (a outra metade espelha as pernas e bracos)
CORRIDA = [
    # contato: perna da frente estendida tocando o chao, a de tras empurrando
    Pose(incl=12, pf=(38, 12), pt=(-38, 30), bf=(-48, 82), bt=(52, 94), torcao=-1.2, cab=(0, 0.3), barra=1.5, vento=1.0, vento_dir=-4),
    # recuo: absorve o peso, joelho dobra, perna de tras recolhe alto
    Pose(incl=15, pf=(18, 34), pt=(-32, 88), bf=(-30, 86), bt=(36, 96), torcao=-0.6, cab=(0, 1.1), barra=2.0, vento=1.0, vento_dir=-2),
    # passagem: perna de apoio na vertical, a outra passando dobrada
    Pose(incl=15, pf=(0, 14), pt=(6, 108), bf=(0, 86), bt=(6, 92), torcao=0, cab=(0, 0.4), barra=2.2, voo=0.5, vento=1.0, vento_dir=-6),
    # impulso: empurra o chao, corpo sobe (voo)
    Pose(incl=13, pf=(-28, 8), pt=(48, 78), bf=(32, 92), bt=(-30, 82), torcao=0.9, cab=(0, -0.6), barra=2.0, voo=2.0, vento=1.0, vento_dir=-8),
]


def ciclo(keys4: list[Pose], n: int, bracos=True) -> list[Pose]:
    meio = [espelhar_pernas(k, bracos) for k in keys4]
    todas = keys4 + meio
    return chaves([(i / 8, k) for i, k in enumerate(todas)], n, loop=True)


def anims_marco() -> dict[str, tuple[list[Pose], int, int]]:
    """nome -> (poses, fps, repetir: -1 loop / 0 uma vez)"""
    A: dict[str, tuple[list[Pose], int, int]] = {}

    respira = replace(NEUTRO, incl=2, bf=(6, 16), bt=(-8, 15), pf=(10, 11), pt=(-6, 3), cab=(0.3, -0.6), x=0.5, barra=0.3)
    parado = chaves([(0, NEUTRO), (0.5, respira)], 12, loop=True)
    parado[9] = replace(parado[9], piscar=True)
    parado = [replace(q, brilho=0.55 + 0.45 * (0.5 + 0.5 * math.sin(2 * math.pi * i / 12))) for i, q in enumerate(parado)]
    A["parado"] = (parado, 10, -1)

    A["correr"] = (ciclo(CORRIDA, 12), 18, -1)

    impulso = Pose(incl=24, pf=(-14, 10), pt=(46, 74), bf=(42, 90), bt=(-42, 80), torcao=1.2, cab=(0.5, 0.8), barra=1.0, vento=0.7)
    A["arrancar"] = (chaves([(0, replace(NEUTRO, incl=10, pf=(14, 24), pt=(-4, 22))), (0.45, impulso), (1, CORRIDA[0])], 4, fase_ciclo=False), 20, 0)

    derrapa = Pose(incl=-14, pf=(46, 4), pt=(-10, 44), bf=(-60, 40), bt=(-92, 30), cab=(1.4, 0), barra=-1.8, vento=0.9, vento_dir=20)
    recupera = Pose(incl=8, pf=(20, 30), pt=(-4, 22), bf=(20, 30), bt=(8, 26), cab=(0.7, 0.6), barra=-0.6, vento=0.5, vento_dir=30)
    A["frear"] = (chaves([(0, CORRIDA[2]), (0.3, derrapa), (0.7, recupera), (1, NEUTRO)], 7), 20, 0)

    virada = Pose(incl=-12, pf=(-26, 26), pt=(22, 52), bf=(-72, 40), bt=(-40, 30), cab=(-1, 0), barra=-2, vento=0.6, vento_dir=-10)
    giro = Pose(incl=8, pf=(26, 62), pt=(-6, 52), bf=(12, 62), bt=(-22, 52), cab=(0, 1), vento=0.5)
    A["virar"] = (chaves([(0, virada), (0.45, giro), (1, CORRIDA[3])], 5), 22, 0)

    # ---- no ar (apoiado=False: altura vem da fisica)
    ar = dict(apoiado=False)
    A["pulo"] = (chaves([
        (0, Pose(y=4, incl=16, pf=(40, 80), pt=(16, 70), bf=(-50, 40), bt=(-60, 30), cab=(0, 1.5), vento=0.5, **ar)),
        (0.5, Pose(y=0, incl=10, pf=(10, 16), pt=(-22, 26), bf=(120, 20), bt=(60, 30), barra=-1, vento=0.7, vento_dir=30, **ar)),
        (1, Pose(y=-2, incl=6, pf=(22, 42), pt=(-8, 52), bf=(150, 0), bt=(-60, 30), barra=-1.5, vento=0.8, vento_dir=40, **ar)),
    ], 3), 24, 0)
    A["subindo"] = (chaves([
        (0, Pose(y=-2, incl=6, pf=(30, 55), pt=(5, 60), bf=(150, 0), bt=(-70, 30), barra=-1.5, vento=0.8, vento_dir=40, **ar)),
        (1, Pose(y=-3, incl=8, pf=(62, 92), pt=(28, 84), bf=(140, -10), bt=(-85, 30), barra=-1, vento=0.8, vento_dir=40, **ar)),
    ], 3), 12, 0)
    A["apice"] = (chaves([
        (0, Pose(y=-3, incl=8, pf=(62, 92), pt=(28, 84), bf=(140, -10), bt=(-85, 30), vento=0.6, vento_dir=10, **ar)),
        (1, Pose(y=-1, incl=7, pf=(44, 58), pt=(10, 48), bf=(112, 12), bt=(-104, 10), vento=0.5, vento_dir=-15, **ar)),
    ], 3), 14, 0)
    queda_a = Pose(incl=6, pf=(26, 24), pt=(-12, 42), bf=(124, -12), bt=(-126, -8), barra=1, vento=0.9, vento_dir=-55, **ar)
    queda_b = replace(queda_a, pf=(18, 30), pt=(-6, 34), bf=(118, -6), bt=(-120, -14))
    A["caindo"] = (chaves([(0, queda_a), (0.5, queda_b)], 4, loop=True), 10, -1)

    agachado = Pose(incl=26, pf=(60, 104), pt=(28, 94), bf=(42, 30), bt=(-12, 40), cab=(0.5, 2.2), barra=-1, vento=0.6, vento_dir=30)
    A["aterrissar"] = (chaves([
        (0, agachado), (0.2, replace(agachado, incl=28, pf=(64, 112), pt=(30, 100), cab=(0.6, 2.6))),
        (0.55, Pose(incl=8, pf=(20, 26), pt=(-4, 20), bf=(20, 26), bt=(-12, 24), cab=(0, 0.5), vento=0.4)),
        (0.75, Pose(incl=2, pf=(6, 2), pt=(-8, 2), bf=(6, 18), bt=(-10, 16), cab=(0, -0.4), voo=0.5, vento=0.35)),
        (1, NEUTRO),
    ], 6, fase_ciclo=False), 22, 0)

    # ---- ataques: antecipacao -> smear -> contato -> continuacao -> acomoda
    def golpe(antecip: Pose, smear: Pose, contato: Pose, segue: Pose, fim: Pose):
        return (chaves([(0, antecip), (0.15, smear), (0.32, contato), (0.5, segue), (0.68, replace(segue, arma="lamina_curta", rastro=None)), (1, fim)], 8, fase_ciclo=False), 30, 0)

    base_ataque = dict(pf=(24, 14), pt=(-20, 12), vento=0.6)
    estoque = dict(pf=(40, 26), pt=(-34, 16), vento=0.9)
    A["ataque_frente"] = golpe(
        Pose(incl=-6, bf=(-150, -25), bt=(30, 40), torcao=-1.5, cab=(-0.5, 0), **base_ataque),
        Pose(incl=18, bf=(100, -5), bt=(-50, 25), arma="lamina", arma_ang=112, rastro=(185, 112), torcao=1, barra=1.5, **estoque),
        Pose(incl=24, bf=(70, -5), bt=(-70, 20), arma="lamina", arma_ang=75, rastro=(112, 75), torcao=1.6, barra=2, cab=(0.6, 0.4), **estoque),
        Pose(incl=22, bf=(42, 10), bt=(-62, 25), arma="lamina", arma_ang=48, rastro=(75, 48), torcao=1.2, barra=2.2, cab=(0.8, 0.6), **estoque),
        replace(NEUTRO, incl=8, pf=(20, 14), pt=(-16, 10)),
    )
    A["ataque_cima"] = golpe(
        Pose(incl=10, bf=(20, 40), bt=(-30, 30), pf=(34, 50), pt=(-10, 40), cab=(0, 1.2), vento=0.5),
        Pose(incl=-4, bf=(150, 0), bt=(-70, 20), arma="lamina", arma_ang=165, rastro=(60, 165), pf=(14, 20), pt=(-12, 14), vento=0.8, vento_dir=30),
        Pose(incl=-10, bf=(182, -5), bt=(-90, 20), arma="lamina", arma_ang=196, rastro=(165, 196), pf=(10, 18), pt=(-14, 16), cab=(-0.5, -0.8), vento=0.9, vento_dir=40),
        Pose(incl=-8, bf=(200, 10), bt=(-80, 20), arma="lamina", arma_ang=214, rastro=(196, 214), pf=(10, 14), pt=(-10, 14), vento=0.6),
        replace(NEUTRO, incl=2, bf=(30, 30)),
    )
    A["ataque_baixo"] = golpe(
        Pose(incl=0, bf=(175, 10), bt=(-40, 20), pf=(16, 12), pt=(-14, 12), cab=(0, -0.6), vento=0.5),
        Pose(incl=24, bf=(82, 0), bt=(-80, 20), arma="lamina", arma_ang=55, rastro=(185, 55), pf=(44, 54), pt=(-24, 30), vento=0.9),
        Pose(incl=32, bf=(36, 0), bt=(-90, 20), arma="lamina", arma_ang=15, rastro=(55, 15), pf=(50, 62), pt=(-26, 36), cab=(0.6, 1.4), barra=2, vento=1.0),
        Pose(incl=30, bf=(14, 10), bt=(-74, 25), arma="lamina", arma_ang=-4, rastro=(15, -4), pf=(48, 58), pt=(-24, 32), cab=(0.6, 1.6), vento=0.7),
        replace(NEUTRO, incl=12, pf=(26, 24), pt=(-14, 16)),
    )

    can = dict(arma="canhao", pf=(18, 10), pt=(-18, 12))
    A["canhao"] = (chaves([
        (0, Pose(incl=4, bf=(45, 40), bt=(-20, 30), vento=0.4, **can)),
        (0.25, Pose(incl=0, bf=(88, 4), bt=(-28, 30), vento=0.4, **can)),
        (0.4, Pose(incl=-9, bf=(100, -4), bt=(-36, 30), cab=(-1, 0), barra=-1, clarao=True, vento=0.8, **can)),
        (0.6, Pose(incl=-5, bf=(96, -2), bt=(-32, 30), cab=(-0.6, 0), vento=0.6, **can)),
        (0.8, Pose(incl=-1, bf=(90, 0), bt=(-28, 30), vento=0.5, **can)),
        (1, Pose(incl=2, bf=(76, 8), bt=(-24, 30), vento=0.4, **can)),
    ], 6, fase_ciclo=False), 24, 0)

    A["morte"] = (poses_morte(marco=True), 16, 0)
    return A


def poses_morte(marco=False) -> list[Pose]:
    """Atingido -> cambaleia -> joelhos cedem -> cai de costas -> quica -> fica caido (12 quadros)."""
    v = dict(vento=0.7) if marco else {}
    return chaves([
        (0, Pose(incl=-24, bf=(-160, 50), bt=(-120, 40), pf=(26, 30), pt=(-10, 24), cab=(-1.5, -0.5), barra=-2, vento_dir=-30, **v)),
        (0.14, Pose(incl=-34, bf=(-176, 30), bt=(-140, 24), pf=(8, 48), pt=(-30, 30), cab=(-1.8, 0), barra=-2, vento_dir=-30, **v)),
        (0.3, Pose(incl=-50, bf=(-170, 12), bt=(-150, 10), pf=(50, 92), pt=(30, 96), cab=(-1.5, 0.5), vento_dir=-40, **v)),
        (0.44, Pose(incl=-72, bf=(-172, 20), bt=(-156, 10), pf=(80, 60), pt=(64, 70), cab=(-1, 0), vento_dir=-60, **v)),
        (0.54, Pose(incl=-92, bf=(-178, 30), bt=(-165, 20), pf=(98, 16), pt=(86, 20), **v)),
        (0.64, Pose(incl=-86, bf=(-168, 40), bt=(-158, 24), pf=(94, 22), pt=(82, 24), voo=1.5, **v)),
        (0.8, Pose(incl=-90, bf=(-182, 14), bt=(-168, 6), pf=(96, 10), pt=(85, 12), brilho=0.5, **v)),
        (1, Pose(incl=-90, bf=(-185, 10), bt=(-170, 5), pf=(95, 8), pt=(85, 12), brilho=0.0, **v)),
    ], 12, fase_ciclo=False)


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
        x, y = soma(g.H, g.u, 0.5)  # cinto
        img.capsula(*soma((x, y), g.f, -5), *soma((x, y), g.f, 5), 0.9, 0.9, rampa((20, 14, 12), (40, 28, 22), (64, 46, 34), (90, 66, 48)), borda=False)

    def cabeca(self, img, g, p):
        cx, cy = g.C
        img.elipse(cx, cy, 4.8, 5.2, PELE_ESCURA)
        capuz = [(cx - 6, cy + 4), (cx - 6.6, cy - 2), (cx - 4, cy - 6.6), (cx + 1, cy - 7.2), (cx + 4.6, cy - 5),
                 (cx + 5.6, cy - 2.2), (cx + 3, cy - 3.4), (cx - 1, cy - 2.6), (cx - 2.4, cy + 2), (cx - 3.4, cy + 5)]
        img.poligono_sombreado(capuz, CAPUZ, cx - 1, cy - 1, 6.5, 6.5)
        img.elipse(cx + 2.6, cy + 2.2, 2.8, 2.3, MASCARA)  # mascara respiratoria
        img.elipse(cx + 3.6, cy + 3.8, 1.7, 1.7, METAL)  # filtro
        img.set(cx + 3.6, cy + 3.8, K)
        img.rect(cx + 0.6, cy - 1.6, 5, 2.4, (24, 10, 20))  # armacao dos oculos

    def arma(self, img, g, p):
        mao, ang, cot, pulso = g.maos["frente"]
        a = p.arma_ang if p.arma_ang is not None else ang
        if p.arma == "cano":
            fim = soma(mao, dirv(a), 15)
            img.capsula(*soma(mao, dirv(a), -3), *fim, 1.4, 1.4, METAL)
            img.capsula(*soma(fim, dirv(a), -2), *fim, 2.2, 2.2, METAL)
            img.elipse(*mao, 2.2, 2.2, self.luva)

    def brilhos(self, img, g, p):
        if p.rastro:
            mao = g.maos["frente"][0]
            rastro(img, mao, p.rastro[0], p.rastro[1], 16, (220, 220, 240), 0.8)
        cx, cy = g.C
        b = max(0.0, min(1.0, p.brilho))
        for x in (cx + 1.2, cx + 3.8):
            img.rect(x, cy - 1.4, 2, 2, ROSA if b > 0.2 else (90, 30, 50))
            img.set(x, cy - 1.4, (255, 190, 210) if b > 0.5 else ROSA)
            img.brilho(x + 1, cy - 0.4, 4, ROSA, 120 * b)


CATADOR = EstiloCatador()


def anims_catador():
    A = {}
    cano = dict(arma="cano")
    curvado = Pose(incl=20, bf=(42, 42), bt=(-8, 22), pf=(10, 10), pt=(-8, 10), **cano)
    A["parado"] = ([replace(q, brilho=0.7 + 0.3 * math.sin(2 * math.pi * i / 10)) for i, q in enumerate(
        chaves([(0, curvado), (0.5, replace(curvado, incl=23, bf=(46, 46), cab=(0.5, 0.9), torcao=0.5, pf=(12, 14)))], 10, loop=True))], 8, -1)

    # andar curvado e pesado: so as pernas espelham, o braco do cano balanca pouco
    passo = [
        Pose(incl=22, pf=(26, 8), pt=(-24, 18), bf=(40, 40), bt=(22, 30), torcao=-0.8, cab=(0, 0.5), **cano),
        Pose(incl=24, pf=(14, 24), pt=(-22, 42), bf=(43, 43), bt=(12, 30), torcao=-0.4, cab=(0, 1.3), **cano),
        Pose(incl=22, pf=(0, 10), pt=(2, 56), bf=(40, 41), bt=(0, 28), cab=(0, 0.4), **cano),
        Pose(incl=20, pf=(-18, 6), pt=(22, 36), bf=(37, 38), bt=(-14, 26), torcao=0.6, cab=(0, -0.3), voo=0.5, **cano),
    ]
    meia = [replace(espelhar_pernas(k, bracos=False), bt=(-k.bt[0], k.bt[1])) for k in passo]
    A["andar"] = (chaves([(i / 8, k) for i, k in enumerate(passo + meia)], 12, loop=True), 12, -1)

    corrida = [
        Pose(incl=30, pf=(40, 14), pt=(-36, 30), bf=(76, 30), bt=(48, 90), torcao=-1, cab=(0, 0.4), barra=1.5, **cano),
        Pose(incl=33, pf=(20, 36), pt=(-30, 86), bf=(78, 32), bt=(30, 92), torcao=-0.5, cab=(0, 1.2), barra=2, **cano),
        Pose(incl=32, pf=(2, 14), pt=(6, 104), bf=(76, 30), bt=(0, 88), cab=(0, 0.4), barra=2, voo=0.5, **cano),
        Pose(incl=30, pf=(-26, 8), pt=(46, 76), bf=(74, 28), bt=(-30, 80), torcao=0.8, cab=(0, -0.5), barra=1.8, voo=1.8, **cano),
    ]
    meia = [replace(espelhar_pernas(k, bracos=False), bt=(-k.bt[0], k.bt[1])) for k in corrida]
    A["correr"] = (chaves([(i / 8, k) for i, k in enumerate(corrida + meia)], 10, loop=True), 16, -1)

    alto = Pose(incl=-12, bf=(-140, 18), bt=(-40, 30), pf=(28, 26), pt=(-20, 20), cab=(-1, -0.4), barra=-1, brilho=1.4, **cano)
    A["preparar"] = (chaves([(0, curvado), (0.55, replace(alto, incl=-6, bf=(-110, 10))), (0.85, alto), (1, replace(alto, x=-0.6))], 6, fase_ciclo=False), 20, 0)
    contato = Pose(incl=34, bf=(60, 0), bt=(-70, 30), pf=(46, 30), pt=(-34, 22), cab=(0.8, 1), barra=2, rastro=(100, 60), **cano)
    A["golpe"] = (chaves([
        (0, Pose(incl=24, bf=(112, -10), bt=(-60, 30), pf=(40, 26), pt=(-30, 20), rastro=(-122, 102), barra=1, **cano)),
        (0.25, contato),
        (0.5, Pose(incl=37, bf=(32, 12), bt=(-62, 30), pf=(46, 32), pt=(-34, 22), cab=(1, 1.4), barra=2.2, **cano)),
        (0.75, Pose(incl=35, bf=(24, 24), bt=(-40, 28), pf=(36, 28), pt=(-26, 18), cab=(0.6, 1.2), **cano)),
        (1, replace(curvado, incl=26, bf=(38, 32))),
    ], 6, fase_ciclo=False), 24, 0)
    A["morte"] = ([replace(q, brilho=max(0.0, 1 - i * 0.09)) for i, q in enumerate(poses_morte())], 16, 0)
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
        img.capsula(*soma(g.N, g.f, -3.5), *soma(g.N, g.f, 3.0), 2.6, 2.4, GOLA)

    def cabeca(self, img, g, p):
        cx, cy = g.C
        img.elipse(*soma(g.C, (-1.2, 0.8)), 1.3, 1.7, PELE, escuro=1)
        img.elipse(cx, cy, 4.4, 5.0, PELE)
        if p.piscar:
            img.set(cx + 2.4, cy + 0.6, PELE[0])
            img.set(cx + 3.4, cy + 0.6, PELE[0])
        else:
            img.set(cx + 2.4, cy - 0.4, K)
            img.set(cx + 2.4, cy + 0.6, K)
        img.set(cx + 4.4, cy + 0.8, PELE[1])
        img.rect(cx + 1.4, cy + 2.4, 3, 1, PELE[0])
        img.rect(cx - 4.4, cy - 0.5, 2, 4, CABELO[1])
        bone = [(cx - 5, cy - 1), (cx - 4.6, cy - 4.6), (cx - 1.5, cy - 6.6), (cx + 2.5, cy - 6.4), (cx + 4.6, cy - 3.6),
                (cx + 8.2, cy - 2.8), (cx + 8.0, cy - 1.6), (cx + 4, cy - 1.8), (cx - 1, cy - 1.6)]
        img.poligono_sombreado(bone, BONE, cx, cy - 3, 6, 4.5)
        img.set(cx + 0.5, cy - 5.2, (255, 140, 66))
        for i in range(-2, 3):  # corrente dourada
            x, y = soma(soma(g.N, g.f, i * 1.1), g.u, -1.5 - abs(i) * 0.4)
            img.set(x, y, OURO)

    def arma(self, img, g, p):
        mao, ang, cot, pulso = g.maos["frente"]
        if p.arma == "pistola":
            fim = soma(mao, dirv(ang), 6.5)
            img.capsula(*soma(mao, dirv(ang), 0.5), *fim, 1.5, 1.4, ARMA)
            img.capsula(*mao, *soma(mao, dirv(ang - 90), 2.2), 1.1, 1.0, ARMA)
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
    A = {}
    arma = dict(arma="pistola")
    base = Pose(incl=2, bf=(12, 26), bt=(-10, 16), pf=(10, 8), pt=(-10, 8), **arma)
    peso = replace(base, x=0.8, incl=3, pf=(12, 12), pt=(-8, 3), bf=(16, 30), cab=(0.4, 0.5), torcao=0.6)
    parado = chaves([(0, base), (0.5, peso)], 10, loop=True)
    parado[6] = replace(parado[6], piscar=True)
    A["parado"] = (parado, 8, -1)
    mira = Pose(incl=-3, bf=(90, 0), bt=(-20, 30), pf=(16, 8), pt=(-16, 10), torcao=1, **arma)
    A["mirar"] = (chaves([(0, base), (0.6, replace(mira, bf=(96, -2), cab=(0.4, -0.3))), (1, mira)], 5, fase_ciclo=False), 24, 0)
    A["atirar"] = (chaves([
        (0, replace(mira, incl=-9, bf=(108, -6), cab=(-1, 0), clarao=True)),
        (0.3, replace(mira, incl=-6, bf=(102, -3), cab=(-0.6, 0))),
        (0.6, replace(mira, incl=-4, bf=(95, 0))),
        (1, mira),
    ], 5, fase_ciclo=False), 24, 0)
    A["morte"] = (poses_morte(), 16, 0)
    return A


PERSONAGENS = {
    "marco": (MARCO, anims_marco),
    "catador": (CATADOR, anims_catador),
    "pistoleiro": (PISTOLEIRO, anims_pistoleiro),
}
