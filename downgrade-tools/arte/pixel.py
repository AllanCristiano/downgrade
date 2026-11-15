"""Mini biblioteca de pixel art sem dependencias (gera PNG RGBA puro).

Principais recursos:
- formas com sombreamento por volume (capsula, elipse, poligono) quantizado em rampas de 4 tons
- contorno externo e contorno interno seletivo (separa membros)
- luz de borda (rim light) para o visual neon
- ruido periodico (texturas que repetem sem emenda), brilhos radiais, dithering
"""
from __future__ import annotations

import math
import random
import struct
import zlib
from pathlib import Path

Cor = tuple  # (r, g, b) ou (r, g, b, a)
Rampa = list  # 4 cores: sombra, base, luz, brilho

BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]

# Luz principal vem de cima/direita/frente; luz de borda (neon da cidade) vem de tras/esquerda
LUZ = (0.55, -0.6, 0.58)
_n = math.sqrt(sum(v * v for v in LUZ))
LUZ = tuple(v / _n for v in LUZ)
BORDA_DIR = (-0.85, -0.5)


def rgba(c: Cor | None) -> tuple[int, int, int, int]:
    if c is None:
        return (0, 0, 0, 0)
    return c if len(c) == 4 else (c[0], c[1], c[2], 255)


def misturar(a: Cor, b: Cor, t: float) -> Cor:
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def escurecer(c: Cor, f: float) -> Cor:
    return tuple(max(0, min(255, round(v * f))) for v in c[:3])


def alfa(c: Cor, a: int) -> Cor:
    return (c[0], c[1], c[2], max(0, min(255, int(a))))


def tom(luz: float) -> int:
    """Quantiza intensidade de luz (0..1) em um indice da rampa."""
    if luz < 0.22:
        return 0
    if luz < 0.52:
        return 1
    if luz < 0.82:
        return 2
    return 3


def luz_normal(nx: float, ny: float, nz: float) -> float:
    return max(0.0, nx * LUZ[0] + ny * LUZ[1] + nz * LUZ[2])


class Img:
    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.px: list[list[tuple | None]] = [[None] * w for _ in range(h)]

    # ================================================================ basico
    def set(self, x: float, y: float, c: Cor | None) -> None:
        x, y = int(math.floor(x)), int(math.floor(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            if c is not None and len(c) == 4 and c[3] < 255:
                if c[3] <= 0:
                    return
                self.px[y][x] = self._compor(self.px[y][x], c)
            else:
                self.px[y][x] = c

    def get(self, x: int, y: int):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y][x]
        return None

    def cheio(self, x: int, y: int) -> bool:
        v = self.get(x, y)
        return v is not None and rgba(v)[3] > 160

    @staticmethod
    def _compor(fundo, c):
        if fundo is None:
            return c
        fr, fg, fb, fa = rgba(fundo)
        a = c[3] / 255
        if fa == 255:
            return (round(fr + (c[0] - fr) * a), round(fg + (c[1] - fg) * a), round(fb + (c[2] - fb) * a))
        na = a + fa / 255 * (1 - a)
        return (
            round((c[0] * a + fr * fa / 255 * (1 - a)) / na),
            round((c[1] * a + fg * fa / 255 * (1 - a)) / na),
            round((c[2] * a + fb * fa / 255 * (1 - a)) / na),
            round(na * 255),
        )

    def rect(self, x: int, y: int, w: int, h: int, c: Cor | None) -> None:
        for yy in range(int(y), int(y + h)):
            for xx in range(int(x), int(x + w)):
                self.set(xx, yy, c)

    def linha(self, x0: float, y0: float, x1: float, y1: float, c: Cor, esp: int = 1) -> None:
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            if esp <= 1:
                self.set(x0, y0, c)
            else:
                o = (esp - 1) // 2
                self.rect(x0 - o, y0 - o, esp, esp, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disco(self, cx: float, cy: float, r: float, c: Cor) -> None:
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                    self.set(x, y, c)

    def anel(self, cx: float, cy: float, r0: float, r1: float, c: Cor) -> None:
        for y in range(int(cy - r1 - 1), int(cy + r1 + 2)):
            for x in range(int(cx - r1 - 1), int(cx + r1 + 2)):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if r0 <= d <= r1:
                    self.set(x, y, c)

    def poligono(self, pts: list[tuple[float, float]], c: Cor) -> None:
        for x, y in self.pixels_poligono(pts):
            self.set(x, y, c)

    @staticmethod
    def pixels_poligono(pts: list[tuple[float, float]]):
        ys = [p[1] for p in pts]
        for y in range(int(math.floor(min(ys))), int(math.ceil(max(ys))) + 1):
            yc = y + 0.5
            xs = []
            for i in range(len(pts)):
                (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
                if (y0 <= yc < y1) or (y1 <= yc < y0):
                    xs.append(x0 + (yc - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for x in range(int(math.floor(xs[i] + 0.5)), int(math.floor(xs[i + 1] + 0.5))):
                    yield x, y

    # ================================================================ formas sombreadas
    def capsula(self, ax, ay, bx, by, ra, rb, rampa: Rampa, borda=True, rim: Cor | None = None, escuro=0) -> None:
        """Capsula afunilada (membros, tronco) com sombreamento por volume."""
        minx = int(min(ax - ra, bx - rb)) - 1
        maxx = int(max(ax + ra, bx + rb)) + 2
        miny = int(min(ay - ra, by - rb)) - 1
        maxy = int(max(ay + ra, by + rb)) + 2
        dx, dy = bx - ax, by - ay
        l2 = dx * dx + dy * dy or 1e-6
        for y in range(miny, maxy):
            for x in range(minx, maxx):
                px, py = x + 0.5, y + 0.5
                t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / l2))
                qx, qy = ax + dx * t, ay + dy * t
                r = ra + (rb - ra) * t
                vx, vy = px - qx, py - qy
                d = math.hypot(vx, vy)
                if d > r:
                    continue
                self._sombrear(x, y, vx / r, vy / r, d, r, rampa, borda, rim, escuro)

    def elipse(self, cx, cy, rx, ry, rampa: Rampa, borda=True, rim: Cor | None = None, escuro=0) -> None:
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                d2 = nx * nx + ny * ny
                if d2 > 1:
                    continue
                d = math.sqrt(d2)
                self._sombrear(x, y, nx, ny, d * min(rx, ry), min(rx, ry), rampa, borda, rim, escuro)

    def poligono_sombreado(self, pts, rampa: Rampa, cx, cy, rx, ry, borda=True, rim: Cor | None = None, escuro=0) -> None:
        """Poligono pintado com as normais de uma elipse (cabelo, roupas)."""
        mask = set(self.pixels_poligono(pts))
        for x, y in mask:
            nx = max(-1, min(1, (x + 0.5 - cx) / rx))
            ny = max(-1, min(1, (y + 0.5 - cy) / ry))
            n = math.hypot(nx, ny)
            if n > 1:
                nx, ny = nx / n, ny / n
            nz = math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
            i = max(0, tom(luz_normal(nx, ny, nz)) - escuro)
            na_borda = borda and any((x + ox, y + oy) not in mask for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if na_borda:
                i = max(0, i - 2)
            cor = rampa[i]
            if rim and na_borda and nx * BORDA_DIR[0] + ny * BORDA_DIR[1] > 0.45:
                cor = rim
            self.set(x, y, cor)

    def _sombrear(self, x, y, nx, ny, d, r, rampa, borda, rim, escuro):
        nz = math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
        i = max(0, tom(luz_normal(nx, ny, nz)) - escuro)
        if borda and d > r - 1.0:
            i = max(0, i - 2)
        cor = rampa[i]
        if rim and d > r - 1.3 and nx * BORDA_DIR[0] + ny * BORDA_DIR[1] > 0.55:
            cor = rim
        self.set(x, y, cor)

    # ================================================================ efeitos
    def brilho(self, cx, cy, r, cor: Cor, a_max=180, passos=True) -> None:
        """Brilho radial (glow). Com passos=True o degrade e quantizado (estilo pixel)."""
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy) / r
                if d >= 1:
                    continue
                v = (1 - d) ** 2
                if passos:
                    v = round(v * 4) / 4
                if v > 0:
                    self.set(x, y, alfa(cor, a_max * v))

    def contorno(self, c: Cor) -> None:
        marcar = []
        for y in range(self.h):
            for x in range(self.w):
                if self.px[y][x] is not None:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if self.cheio(x + dx, y + dy):
                        marcar.append((x, y))
                        break
        for x, y in marcar:
            self.px[y][x] = c

    def colar(self, outra: "Img", ox: int, oy: int) -> None:
        for y in range(outra.h):
            for x in range(outra.w):
                c = outra.px[y][x]
                if c is not None:
                    self.set(ox + x, oy + y, c)

    def recorte(self, x: int, y: int, w: int, h: int) -> "Img":
        n = Img(w, h)
        for yy in range(h):
            for xx in range(w):
                n.px[yy][xx] = self.get(x + xx, y + yy)
        return n

    def escalar(self, f: int) -> "Img":
        n = Img(self.w * f, self.h * f)
        for y in range(self.h):
            for x in range(self.w):
                c = self.px[y][x]
                if c is not None:
                    n.rect(x * f, y * f, f, f, c)
        return n

    # ================================================================ salvar
    def salvar(self, caminho: Path | str) -> None:
        caminho = Path(caminho)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        linhas = bytearray()
        for row in self.px:
            linhas.append(0)
            for c in row:
                linhas += bytes(rgba(c))

        def chunk(t: bytes, d: bytes) -> bytes:
            return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

        png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 6, 0, 0, 0))
        png += chunk(b"IDAT", zlib.compress(bytes(linhas), 9)) + chunk(b"IEND", b"")
        caminho.write_bytes(png)


def grade(quadros: list[Img], colunas: int = 16) -> Img:
    """Spritesheet em grade (Phaser le em ordem, linha por linha)."""
    w, h = quadros[0].w, quadros[0].h
    cols = min(colunas, len(quadros))
    linhas = math.ceil(len(quadros) / cols)
    f = Img(w * cols, h * linhas)
    for i, q in enumerate(quadros):
        f.colar(q, (i % cols) * w, (i // cols) * h)
    return f


def ruido(w: int, h: int, celula: int, seed: int) -> list[list[float]]:
    """Value noise periodico (repete sem emenda em w x h)."""
    r = random.Random(seed)
    gw, gh = max(1, w // celula), max(1, h // celula)
    g = [[r.random() for _ in range(gw)] for _ in range(gh)]
    out = []
    for y in range(h):
        fy = y / celula
        y0 = int(fy) % gh
        y1 = (y0 + 1) % gh
        ty = fy - int(fy)
        ty = ty * ty * (3 - 2 * ty)
        linha = []
        for x in range(w):
            fx = x / celula
            x0 = int(fx) % gw
            x1 = (x0 + 1) % gw
            tx = fx - int(fx)
            tx = tx * tx * (3 - 2 * tx)
            a = g[y0][x0] + (g[y0][x1] - g[y0][x0]) * tx
            b = g[y1][x0] + (g[y1][x1] - g[y1][x0]) * tx
            linha.append(a + (b - a) * ty)
        out.append(linha)
    return out


def fbm(w: int, h: int, seed: int, celulas=(16, 8, 4)) -> list[list[float]]:
    camadas = [ruido(w, h, c, seed + i * 17) for i, c in enumerate(celulas)]
    pesos = [0.55, 0.3, 0.15][: len(celulas)]
    return [[sum(camadas[k][y][x] * pesos[k] for k in range(len(camadas))) for x in range(w)] for y in range(h)]


# ================================================================ fonte 3x5
FONTE = {
    "A": [".#.", "#.#", "###", "#.#", "#.#"], "B": ["##.", "#.#", "##.", "#.#", "##."],
    "C": [".##", "#..", "#..", "#..", ".##"], "D": ["##.", "#.#", "#.#", "#.#", "##."],
    "E": ["###", "#..", "##.", "#..", "###"], "F": ["###", "#..", "##.", "#..", "#.."],
    "G": [".##", "#..", "#.#", "#.#", ".##"], "H": ["#.#", "#.#", "###", "#.#", "#.#"],
    "I": ["###", ".#.", ".#.", ".#.", "###"], "J": ["..#", "..#", "..#", "#.#", ".#."],
    "L": ["#..", "#..", "#..", "#..", "###"], "M": ["#.#", "###", "###", "#.#", "#.#"],
    "N": ["##.", "#.#", "#.#", "#.#", "#.#"], "O": ["###", "#.#", "#.#", "#.#", "###"],
    "P": ["##.", "#.#", "##.", "#..", "#.."], "Q": ["###", "#.#", "#.#", "###", "..#"],
    "R": ["##.", "#.#", "##.", "#.#", "#.#"], "S": [".##", "#..", ".#.", "..#", "##."],
    "T": ["###", ".#.", ".#.", ".#.", ".#."], "U": ["#.#", "#.#", "#.#", "#.#", "###"],
    "V": ["#.#", "#.#", "#.#", "#.#", ".#."], "X": ["#.#", "#.#", ".#.", "#.#", "#.#"],
    "Z": ["###", "..#", ".#.", "#..", "###"], "0": ["###", "#.#", "#.#", "#.#", "###"],
    "1": [".#.", "##.", ".#.", ".#.", "###"], "9": ["###", "#.#", "###", "..#", "###"],
    "-": ["...", "...", "###", "...", "..."], ":": ["...", ".#.", "...", ".#.", "..."],
    "!": [".#.", ".#.", ".#.", "...", ".#."], " ": ["...", "...", "...", "...", "..."],
}


def texto(img: Img, x: int, y: int, s: str, c: Cor, escala: int = 1, cores: dict[int, Cor] | None = None) -> int:
    """Escreve com a fonte 3x5. Retorna a largura em px."""
    for i, ch in enumerate(s.upper()):
        g = FONTE.get(ch, FONTE[" "])
        cor = (cores or {}).get(i, c)
        for gy, linha in enumerate(g):
            for gx, v in enumerate(linha):
                if v == "#":
                    img.rect(x + (i * 4 + gx) * escala, y + gy * escala, escala, escala, cor)
    return (len(s) * 4 - 1) * escala
