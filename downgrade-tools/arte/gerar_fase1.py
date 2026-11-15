"""DOWNGRADE — gera toda a pixel art da Fase 1 (O Lixao).

Uso:  python gerar_fase1.py <pasta-assets> [pasta-preview]
      (ex: python gerar_fase1.py ../../downgrade-game/public/assets)

Saida em <assets>/:
  tiles/lixao.png               tileset 32x32 (nomes em cenario.NOMES_TILES, firstgid 1)
  fundos/lixao-*.png            5 camadas de parallax (480x272, desenhadas em 2x no jogo)
  sprites/*.png                 personagens (64x64), objetos animados, efeitos, luzes
  sprites/pacote.json           asset pack do Phaser (load.pack)
  sprites/animacoes.json        animacoes do Phaser (criadas automaticamente ao carregar)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cenario
import efeitos
from personagens import PERSONAGENS, desenhar
from pixel import Img, grade

URL_BASE = "assets"


class Pacote:
    def __init__(self, raiz: Path):
        self.raiz = raiz
        self.arquivos: list[dict] = []
        self.anims: list[dict] = []

    def folha(self, chave: str, quadros: list[Img], anims: dict[str, tuple[list[int], int, int]] | None = None, colunas=16):
        """Salva uma spritesheet e registra animacoes: nome -> (indices, fps, repeat)."""
        img = grade(quadros, colunas)
        img.salvar(self.raiz / "sprites" / f"{chave}.png")
        self.arquivos.append({
            "type": "spritesheet", "key": chave, "url": f"{URL_BASE}/sprites/{chave}.png",
            "frameConfig": {"frameWidth": quadros[0].w, "frameHeight": quadros[0].h},
        })
        for nome, (idx, fps, rep) in (anims or {}).items():
            self.anims.append({
                "key": f"{chave}-{nome}", "frameRate": fps, "repeat": rep,
                "frames": [{"key": chave, "frame": i} for i in idx],
            })

    def imagem(self, chave: str, img: Img, pasta="sprites"):
        img.salvar(self.raiz / pasta / f"{chave}.png")
        self.arquivos.append({"type": "image", "key": chave, "url": f"{URL_BASE}/{pasta}/{chave}.png"})

    def salvar(self):
        self.arquivos.append({"type": "animation", "key": "animacoes", "url": f"{URL_BASE}/sprites/animacoes.json"})
        (self.raiz / "sprites").mkdir(parents=True, exist_ok=True)
        (self.raiz / "sprites" / "pacote.json").write_text(
            json.dumps({"downgrade": {"files": self.arquivos}}, indent=1), encoding="utf-8")
        (self.raiz / "sprites" / "animacoes.json").write_text(json.dumps({"anims": self.anims}), encoding="utf-8")


def sequencia(grupos: dict[str, tuple[list, int, int]]):
    """Achata {nome: (quadros, fps, rep)} em (lista de quadros, {nome: (indices, fps, rep)})."""
    quadros, anims = [], {}
    for nome, (qs, fps, rep) in grupos.items():
        anims[nome] = (list(range(len(quadros), len(quadros) + len(qs))), fps, rep)
        quadros += qs
    return quadros, anims


def main() -> None:
    assets = Path(sys.argv[1])
    preview = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    p = Pacote(assets)

    # ---- personagens
    sprites_prev = {}
    for chave, (estilo, fn) in PERSONAGENS.items():
        grupos = {nome: ([desenhar(pose, estilo) for pose in poses], fps, rep) for nome, (poses, fps, rep) in fn().items()}
        quadros, anims = sequencia(grupos)
        p.folha(chave, quadros, anims)
        sprites_prev[chave] = grupos
        print(f"  {chave}: {len(quadros)} quadros, {len(anims)} animacoes")

    # ---- objetos animados do cenario
    p.folha("barril_fogo", cenario.barril_fogo(), {"loop": (list(range(6)), 12, -1)})
    p.folha("neon", cenario.letreiro_neon(), {"loop": ([0, 1, 0, 1, 0, 2, 0, 1, 0, 3, 0, 1], 8, -1)})
    p.folha("tv", cenario.tv(), {"loop": (list(range(4)), 14, -1)})
    p.folha("poste", cenario.poste(), {"loop": ([0] * 14 + [1, 0, 1], 10, -1)})
    p.folha("barril_toxico", cenario.barril_toxico(), {"loop": (list(range(4)), 6, -1)})
    s = cenario.saida()
    quadros, anims = sequencia({"fechada": (s["fechada"], 3, -1), "abrindo": (s["abrindo"], 14, 0), "aberta": (s["aberta"], 4, -1)})
    p.folha("saida", quadros, anims)
    for chave, img in cenario.luzes().items():
        p.imagem(chave, img)

    # ---- efeitos
    p.folha("corte", efeitos.corte(), {"golpe": (list(range(5)), 36, 0)})
    p.folha("faisca", efeitos.faisca(), {"estouro": (list(range(6)), 30, 0)})
    p.folha("sangue", efeitos.sangue(), {"respingo": (list(range(6)), 24, 0)})
    p.folha("clarao", efeitos.clarao(), {"tiro": (list(range(3)), 30, 0)})
    p.folha("poeira", efeitos.poeira(), {"nuvem": (list(range(6)), 20, 0)})
    p.folha("tiro_canhao", efeitos.tiro_canhao(), {"voo": ([0, 1], 16, -1)})
    p.folha("impacto_canhao", efeitos.impacto_canhao(), {"estouro": (list(range(5)), 24, 0)})
    p.imagem("bala", efeitos.bala((255, 42, 109)))
    p.imagem("bala_rebatida", efeitos.bala((0, 240, 255)))
    p.imagem("fragmento", efeitos.fragmento())
    p.salvar()

    # ---- tileset e fundos (carregados pela fase, fora do pacote)
    ts = cenario.tileset()
    ts.salvar(assets / "tiles" / "lixao.png")
    camadas = []
    for chave, fn, fator in cenario.FUNDOS:
        img = fn()
        img.salvar(assets / "fundos" / f"{chave}.png")
        camadas.append(img)
        print(f"  fundo {chave} (parallax {fator})")

    if preview:
        preview.mkdir(parents=True, exist_ok=True)
        ts.escalar(2).salvar(preview / "tileset.png")
        cena = Img(cenario.FW, cenario.FH)
        for c in camadas:
            cena.colar(c, 0, 0)
        ids = {n: i for i, n in enumerate(cenario.NOMES_TILES)}

        def tile(nome, cx, cy):
            i = ids[nome]
            cena.colar(ts.recorte(i % 8 * 32, i // 8 * 32, 32, 32), cx, cy)

        for x in range(0, cenario.FW, 32):
            tile(f"chao_topo_{x // 32 % 4 + 1}", x, 208)
            tile(f"chao_meio_{x // 32 % 3 + 1}", x, 240)
        for i, cor in enumerate(("vermelho", "azul", "verde", "amarelo")):
            tile(f"fardo_{cor}", 260 + i * 32, 130)
        for i in range(6):
            tile(f"carro_{i + 1}", 330 + i % 3 * 32, 144 + i // 3 * 32)
        tile("cadaver_1", 120, 176)
        tile("cadaver_2", 152, 176)
        cena.colar(cenario.letreiro_neon()[0], 190, 164)
        cena.colar(cenario.barril_fogo()[2], 20, 160)
        cena.colar(cenario.poste()[0], 440, 112)
        cena.colar(s["fechada"][0], 425, 112 + 0)
        cena.colar(sprites_prev["marco"]["parado"][0][0], 60, 144)
        cena.colar(sprites_prev["catador"]["andar"][0][2], 210, 144)
        cena.colar(sprites_prev["pistoleiro"]["mirar"][0][2], 270, 66)
        cena.colar(efeitos.corte()[1], 80, 112)
        cena.escalar(2).salvar(preview / "cena.png")
    print("arte gerada em", assets)


if __name__ == "__main__":
    main()
