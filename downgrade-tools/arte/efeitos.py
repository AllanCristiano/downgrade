"""Efeitos visuais: corte, faiscas, sangue, clarao, poeira, projeteis."""
from __future__ import annotations

import math
import random

from pixel import Img, alfa

CIANO = (0, 240, 255)
BRANCO = (240, 250, 255)
ROSA = (255, 42, 109)
AMARELO = (255, 209, 102)
SANGUE = [(70, 4, 20), (130, 10, 36), (190, 24, 52), (240, 70, 90)]


def corte() -> list[Img]:
    """Arco da lamina de plasma, 96x96, centro do arco em (24, 48)."""
    q = []
    cx, cy = 24, 48
    quadros = [(-80, -10, 1.0), (-80, 70, 1.0), (-50, 80, 0.75), (-10, 85, 0.45), (30, 85, 0.2)]
    for i, (a0, a1, forca) in enumerate(quadros):
        img = Img(96, 96)
        for y in range(96):
            for x in range(96):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                ang = math.degrees(math.atan2(y + 0.5 - cy, x + 0.5 - cx))
                if not (a0 <= ang <= a1):
                    continue
                prog = (ang - a0) / max(1, a1 - a0)  # 1 = ponta do golpe
                r_ext = 40
                r_int = 40 - (6 + 16 * prog) * forca
                if r_int <= d <= r_ext:
                    borda = d > r_ext - 1.5
                    a = (90 + 160 * prog) * forca
                    if borda:
                        img.set(x, y, alfa(BRANCO, min(255, a + 60)))
                    elif d > r_ext - 4:
                        img.set(x, y, alfa(CIANO, a))
                    else:
                        img.set(x, y, alfa((0, 160, 220), a * 0.55))
        r = random.Random(i)
        for _ in range(int(10 * forca)):
            ang = math.radians(r.uniform(a0, a1))
            d = r.uniform(38, 46)
            img.set(cx + math.cos(ang) * d, cy + math.sin(ang) * d, alfa(BRANCO, 220 * forca))
        q.append(img)
    return q


def faisca() -> list[Img]:
    """Bala rebatida: estrela de faiscas 32x32."""
    q = []
    for f in range(6):
        img = Img(32, 32)
        r = random.Random(7)
        raio = 4 + f * 2.2
        forca = 1 - f / 6
        img.brilho(16, 16, 10 - f, CIANO, 200 * forca)
        for k in range(8):
            a = math.radians(k * 45 + r.uniform(-10, 10))
            comp = raio * (1.3 if k % 2 == 0 else 0.8)
            ini = max(0, raio - 6)
            img.linha(16 + math.cos(a) * ini, 16 + math.sin(a) * ini, 16 + math.cos(a) * comp, 16 + math.sin(a) * comp,
                      alfa(BRANCO if k % 2 == 0 else CIANO, 255 * forca))
        if f < 2:
            img.disco(16, 16, 3 - f, BRANCO)
        q.append(img)
    return q


def sangue() -> list[Img]:
    """Respingo direcional (para a direita), 48x48, origem em (12, 24)."""
    q = []
    r = random.Random(3)
    gotas = [(r.uniform(-50, 50), r.uniform(30, 120), r.uniform(1, 2.6)) for _ in range(22)]
    for f in range(6):
        img = Img(48, 48)
        t = (f + 1) / 6
        for ang, vel, tam in gotas:
            a = math.radians(ang)
            d = vel * t * 0.28
            x = 12 + math.cos(a) * d
            y = 24 + math.sin(a) * d + 18 * t * t
            s = tam * (1 - t * 0.5)
            img.disco(x, y, s, SANGUE[2] if tam > 1.8 else SANGUE[3])
            if s > 1.2:
                img.set(x - 1, y - 1, SANGUE[3])
        if f < 2:
            img.disco(12, 24, 6 - f * 2, SANGUE[1])
        q.append(img)
    return q


def clarao() -> list[Img]:
    q = []
    for f in range(3):
        img = Img(24, 24)
        img.brilho(8, 12, 10 - f * 3, AMARELO, 200)
        for k in (-35, 0, 35):
            a = math.radians(k)
            comp = 14 - f * 4
            img.linha(6, 12, 6 + math.cos(a) * comp, 12 + math.sin(a) * comp, (255, 240, 200))
        img.disco(7, 12, 3 - f, (255, 255, 230))
        q.append(img)
    return q


def poeira() -> list[Img]:
    q = []
    r = random.Random(5)
    nuvens = [(r.uniform(-1, 1), r.uniform(0.2, 1), r.uniform(2, 4)) for _ in range(7)]
    for f in range(6):
        img = Img(32, 16)
        t = (f + 1) / 6
        for dx, dy, tam in nuvens:
            x = 16 + dx * 13 * t
            y = 13 - dy * 6 * t
            img.disco(x, y, tam * (0.6 + t * 0.6), (120, 100, 140, int(180 * (1 - t))))
            img.disco(x - 0.5, y - 0.8, tam * 0.5, (170, 150, 190, int(160 * (1 - t))))
        q.append(img)
    return q


def bala(cor) -> Img:
    img = Img(16, 6)
    for x in range(16):
        a = int(255 * (x / 15) ** 1.5)
        img.set(x, 2, alfa(cor, a))
        img.set(x, 3, alfa(cor, a))
        if x > 8:
            img.set(x, 1, alfa(cor, a * 0.4))
            img.set(x, 4, alfa(cor, a * 0.4))
    img.rect(13, 2, 3, 2, BRANCO)
    return img


def tiro_canhao() -> list[Img]:
    q = []
    for f in range(2):
        img = Img(24, 12)
        for x in range(24):
            a = int(230 * (x / 23) ** 1.3)
            larg = 1 + (x / 23) * 3
            for dy in range(-int(larg), int(larg) + 1):
                img.set(x, 6 + dy, alfa(AMARELO if abs(dy) > 1 else (255, 244, 210), a))
        img.disco(19 + f, 6, 3.4, (255, 250, 230))
        q.append(img)
    return q


def impacto_canhao() -> list[Img]:
    q = []
    for f in range(5):
        img = Img(32, 32)
        t = (f + 1) / 5
        img.anel(16, 16, 3 + t * 9, 5 + t * 10, alfa(AMARELO, 230 * (1 - t)))
        img.brilho(16, 16, 12 * (1 - t) + 3, (255, 240, 200), 220 * (1 - t))
        q.append(img)
    return q


def fragmento() -> Img:
    img = Img(5, 5)
    img.brilho(2.5, 2.5, 3, CIANO, 200)
    img.rect(2, 2, 1, 1, BRANCO)
    return img
