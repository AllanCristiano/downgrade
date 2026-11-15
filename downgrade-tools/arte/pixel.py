"""Mini biblioteca de pixel art sem dependencias (gera PNG RGBA puro)."""
from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

Cor = tuple  # (r, g, b) ou (r, g, b, a)

BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def rgba(c: Cor | None) -> tuple[int, int, int, int]:
    if c is None:
        return (0, 0, 0, 0)
    return c if len(c) == 4 else (c[0], c[1], c[2], 255)


def misturar(a: Cor, b: Cor, t: float) -> Cor:
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def escurecer(c: Cor, f: float) -> Cor:
    return tuple(max(0, min(255, round(v * f))) for v in c[:3])


class Img:
    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.px: list[list[tuple | None]] = [[None] * w for _ in range(h)]

    # ---------------------------------------------------------------- basico
    def set(self, x: float, y: float, c: Cor | None) -> None:
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            if c is not None and len(c) == 4 and c[3] < 255:
                self.px[y][x] = self._compor(self.px[y][x], c)
            else:
                self.px[y][x] = c

    def get(self, x: int, y: int):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y][x]
        return None

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
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def linha(self, x0: float, y0: float, x1: float, y1: float, c: Cor, esp: int = 1) -> None:
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.carimbo(x0, y0, c, esp)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def carimbo(self, x: int, y: int, c: Cor, esp: int) -> None:
        if esp <= 1:
            self.set(x, y, c)
            return
        o = (esp - 1) // 2
        self.rect(x - o, y - o, esp, esp, c)

    def disco(self, cx: float, cy: float, r: float, c: Cor) -> None:
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.set(x, y, c)

    def anel(self, cx: float, cy: float, r0: float, r1: float, c: Cor) -> None:
        for y in range(int(cy - r1 - 1), int(cy + r1 + 2)):
            for x in range(int(cx - r1 - 1), int(cx + r1 + 2)):
                d = math.hypot(x - cx, y - cy)
                if r0 <= d <= r1:
                    self.set(x, y, c)

    def colar(self, outra: "Img", ox: int, oy: int) -> None:
        for y in range(outra.h):
            for x in range(outra.w):
                c = outra.px[y][x]
                if c is not None:
                    self.set(ox + x, oy + y, c)

    def contorno(self, c: Cor) -> None:
        """Contorno de 1px em volta de tudo que nao e transparente (estilo pixel art)."""
        marcar = []
        for y in range(self.h):
            for x in range(self.w):
                if self.px[y][x] is not None:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    v = self.get(x + dx, y + dy)
                    if v is not None and rgba(v)[3] > 200:
                        marcar.append((x, y))
                        break
        for x, y in marcar:
            self.px[y][x] = c

    def espelhar(self) -> "Img":
        n = Img(self.w, self.h)
        n.px = [list(reversed(r)) for r in self.px]
        return n

    def escalar(self, f: int) -> "Img":
        n = Img(self.w * f, self.h * f)
        for y in range(self.h):
            for x in range(self.w):
                c = self.px[y][x]
                if c is not None:
                    n.rect(x * f, y * f, f, f, c)
        return n

    # ---------------------------------------------------------------- salvar
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


def folha(quadros: list[Img]) -> Img:
    """Junta quadros do mesmo tamanho lado a lado (spritesheet)."""
    w, h = quadros[0].w, quadros[0].h
    f = Img(w * len(quadros), h)
    for i, q in enumerate(quadros):
        f.colar(q, i * w, 0)
    return f


# Fonte 3x5 para letreiros
FONTE = {
    "A": [".#.", "#.#", "###", "#.#", "#.#"],
    "T": ["###", ".#.", ".#.", ".#.", ".#."],
    "E": ["###", "#..", "##.", "#..", "###"],
    "R": ["##.", "#.#", "##.", "#.#", "#.#"],
    "O": ["###", "#.#", "#.#", "#.#", "###"],
    "9": ["###", "#.#", "###", "..#", "###"],
    "F": ["###", "#..", "##.", "#..", "#.."],
    "I": ["###", ".#.", ".#.", ".#.", "###"],
    "D": ["##.", "#.#", "#.#", "#.#", "##."],
    " ": ["...", "...", "...", "...", "..."],
}


def texto(img: Img, x: int, y: int, s: str, c: Cor, escala: int = 1, cores_por_letra: dict[int, Cor] | None = None) -> None:
    for i, ch in enumerate(s):
        g = FONTE[ch]
        cor = (cores_por_letra or {}).get(i, c)
        for gy, linha in enumerate(g):
            for gx, v in enumerate(linha):
                if v == "#":
                    img.rect(x + (i * 4 + gx) * escala, y + gy * escala, escala, escala, cor)
