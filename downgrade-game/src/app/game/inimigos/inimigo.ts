import Phaser from 'phaser';

/** O que um inimigo precisa saber sobre a fase para agir. A cena implementa isso. */
export interface Mundo {
  readonly marco: Phaser.GameObjects.Rectangle;
  marcoVivo(): boolean;
  /** true se nao ha nenhum solido entre os dois pontos. */
  temVisao(de: Phaser.GameObjects.Rectangle, para: Phaser.GameObjects.Rectangle): boolean;
  matarMarco(motivo: string): void;
  dispararBala(x: number, y: number, angulo: number): void;
}

export abstract class Inimigo extends Phaser.GameObjects.Rectangle {
  vivo = true;
  direcao = -1;

  constructor(scene: Phaser.Scene, x: number, y: number, protected readonly cor: number) {
    super(scene, x, y, 22, 40, cor);
    scene.add.existing(this);
  }

  get corpo(): Phaser.Physics.Arcade.Body {
    return this.body as Phaser.Physics.Arcade.Body;
  }

  /** Chamado a cada frame pela cena. */
  abstract pensar(mundo: Mundo): void;

  /** Morre com 1 golpe. O corpo voa na direcao do golpe. */
  morrer(direcaoGolpe: number): void {
    if (!this.vivo) return;
    this.vivo = false;
    this.corpo.enable = false;
    this.setFillStyle(0x44394f);
    this.scene.tweens.add({
      targets: this,
      x: this.x + direcaoGolpe * 50,
      y: this.y + 12,
      angle: 90 * direcaoGolpe,
      alpha: 0.25,
      duration: 380,
      ease: 'Cubic.easeOut',
      onComplete: () => this.destroy(),
    });
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
