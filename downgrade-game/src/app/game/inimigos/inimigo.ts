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

  constructor(scene: Phaser.Scene, x: number, y: number, readonly folha: string) {
    super(scene, x, y, folha, 0);
    scene.add.existing(this);
    this.setDepth(2);
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

  /** Morre com 1 golpe: animacao de queda e o corpo fica no chao. */
  morrer(direcaoGolpe: number): void {
    if (!this.vivo) return;
    this.vivo = false;
    this.clearTint();
    // cai para longe do golpe: vira o rosto para o atacante
    this.direcao = -direcaoGolpe;
    this.olhar();
    this.play(`${this.folha}-morte`);
    this.corpo.setVelocity(direcaoGolpe * 170, -150);
    this.corpo.setDragX(420);
    this.setDepth(1);
  }

  /** Acelera/freia ate a velocidade alvo (inimigos tambem tem peso). */
  protected acelerar(alvo: number, taxa: number): void {
    const dt = this.scene.game.loop.delta / 1000 / this.scene.physics.world.timeScale;
    const v = this.corpo.velocity.x;
    const passo = taxa * dt;
    this.corpo.setVelocityX(v < alvo ? Math.min(alvo, v + passo) : Math.max(alvo, v - passo));
  }

  protected animar(nome: string): void {
    this.play(`${this.folha}-${nome}`, true);
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

  /** Espera em tempo de jogo (respeita a camera lenta do Overtime e o hit-stop). */
  protected depois(ms: number, acao: () => void): void {
    this.scene.time.delayedCall(ms, () => {
      if (this.vivo && this.active) acao();
    });
  }
}
