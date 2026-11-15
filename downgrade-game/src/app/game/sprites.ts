import Phaser from 'phaser';

/**
 * Spritesheets gerados por downgrade-tools/arte/gerar_arte_fase1.py.
 * Todos os personagens olham para a DIREITA (flipX para a esquerda).
 */
const FOLHAS = [
  { chave: 'marco', url: 'assets/sprites/marco.png', w: 32, h: 48 },
  { chave: 'catador', url: 'assets/sprites/catador.png', w: 32, h: 48 },
  { chave: 'pistoleiro', url: 'assets/sprites/pistoleiro.png', w: 32, h: 48 },
  { chave: 'saida', url: 'assets/sprites/saida.png', w: 32, h: 80 },
  { chave: 'corte', url: 'assets/sprites/corte.png', w: 48, h: 48 },
];

/** Quadros fixos de cada folha (ver ordem no gerador). */
export const QUADRO = {
  marco: { subindo: 10, caindo: 11, morto: 15 },
  catador: { preparando: 4, golpe: 5, parado: 6 },
  pistoleiro: { mirando: 2, tiro: 3 },
  saida: { fechada: 0, aberta: 1 },
} as const;

/** Corpo de colisao dentro do quadro 32x48 (pes na base do quadro). */
export const CORPO_HUMANO = { w: 14, h: 40, offsetX: 9, offsetY: 8 };

export function carregarSprites(scene: Phaser.Scene): void {
  for (const f of FOLHAS) {
    if (!scene.textures.exists(f.chave)) {
      scene.load.spritesheet(f.chave, f.url, { frameWidth: f.w, frameHeight: f.h });
    }
  }
}

export function criarAnimacoes(scene: Phaser.Scene): void {
  const a = scene.anims;
  const def = (key: string, textura: string, frames: number[], frameRate: number, repeat = -1) => {
    if (!a.exists(key)) a.create({ key, frames: a.generateFrameNumbers(textura, { frames }), frameRate, repeat });
  };
  def('marco-parado', 'marco', [0, 1, 2, 3], 5);
  def('marco-correr', 'marco', [4, 5, 6, 7, 8, 9], 14);
  def('marco-ataque', 'marco', [13, 14], 16, 0);
  def('catador-andar', 'catador', [0, 1, 2, 3], 7);
  def('pistoleiro-parado', 'pistoleiro', [0, 1], 3);
  def('corte', 'corte', [0, 1, 2], 25, 0);
}
