import Phaser from 'phaser';
import { CORPO_HUMANO } from '../sprites';

export interface Ponto {
  x: number;
  y: number;
}

/** O que um inimigo precisa saber sobre a fase para agir. A cena implementa isso. */
export interface Mundo {
  readonly marco: Phaser.GameObjects.Sprite;
  marcoVivo(): boolean;
  /** true se nao ha nenhum solido entre os dois pontos. */
  temVisao(de: Ponto, para: Ponto): boolean;
  matarMarco(motivo: string): void;
  dispararBala(x: number, y: number, angulo: number): void;
}

export abstract class Inimigo extends Phaser.GameObjects.Sprite {
  vivo = true;
  direcao = -1;

  constructor(scene: Phaser.Scene, x: number, y: number, textura: string) {
    super(scene, x, y, textura, 0);
    scene.add.existing(this);
  }

  get corpo(): Phaser.Physics.Arcade.Body {
    return this.body as Phaser.Physics.Arcade.Body;
  }

  /** Chamado pela cena depois de adicionar ao grupo de fisica. */
  ajustarCorpo(): void {
    this.corpo.setSize(CORPO_HUMANO.w, CORPO_HUMANO.h).setOffset(CORPO_HUMANO.offsetX, CORPO_HUMANO.offsetY);
  }

  /** Chamado a cada frame pela cena. */
  abstract pensar(mundo: Mundo): void;

  /** Morre com 1 golpe. O corpo voa na direcao do golpe. */
  morrer(direcaoGolpe: number): void {
    if (!this.vivo) return;
    this.vivo = false;
    this.corpo.enable = false;
    this.stop();
    this.setTint(0x8a7a9a);
    this.scene.tweens.add({
      targets: this,
      x: this.x + direcaoGolpe * 50,
      y: this.y + 14,
      angle: 90 * direcaoGolpe,
      alpha: 0.2,
      duration: 420,
      ease: 'Cubic.easeOut',
      onComplete: () => this.destroy(),
    });
  }

  protected olhar(): void {
    this.setFlipX(this.direcao < 0);
  }

  /** Pisca branco (telegrafa um ataque). */
  protected piscar(ms = 90): void {
    this.setTintFill(0xffffff);
    this.depois(ms, () => this.clearTint());
  }

  protected veMarco(mundo: Mundo, alcance: number, alturaMax: number): boolean {
    if (!mundo.marcoVivo()) return false;
    const dx = mundo.marco.x - this.x;
    const dy = mundo.marco.y - this.y;
    return Math.abs(dx) <= alcance && Math.abs(dy) <= alturaMax && mundo.temVisao(this, mundo.marco);
  }

  /** Espera em tempo de jogo (respeita a camera lenta do Overtime). */
  protected depois(ms: number, acao: () => void): void {
    this.scene.time.delayedCall(ms, () => {
      if (this.vivo && this.active) acao();
    });
  }
}
