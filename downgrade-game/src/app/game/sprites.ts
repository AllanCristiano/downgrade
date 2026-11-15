import Phaser from 'phaser';

/**
 * Sprites, efeitos e animacoes vem de um asset pack gerado por
 * downgrade-tools/arte/gerar_fase1.py (assets/sprites/pacote.json + animacoes.json).
 * Animacoes se chamam "<folha>-<nome>", ex: "marco-correr", "catador-golpe".
 * Todos os personagens olham para a DIREITA (flipX para a esquerda).
 */
export const PACOTE_SPRITES = 'assets/sprites/pacote.json';

/** Quadros de personagem sao 64x64 com os pes na base. Corpo de colisao 14x40. */
export const CORPO_HUMANO = { w: 14, h: 40, offsetX: 25, offsetY: 24 };
export const MEIA_ALTURA_SPRITE = 32;

export function carregarSprites(scene: Phaser.Scene): void {
  if (!scene.textures.exists('marco')) scene.load.pack('downgrade', PACOTE_SPRITES);
}
