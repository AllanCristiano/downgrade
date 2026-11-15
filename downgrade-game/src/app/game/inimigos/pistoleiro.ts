import Phaser from 'phaser';
import { Inimigo, Mundo } from './inimigo';

const VISAO = 300;
const ALTURA_VISAO = 140;
const MIRA_MS = 650; // laser de mira visivel antes do tiro
const RECARGA_MS = 1100;
/** Posicao do cano da arma em relacao ao centro do sprite (olhando para a direita). */
const CANO = { x: 22, y: -6 };

type Estado = 'vigiando' | 'mirando' | 'recarga';

/** Pistoleiro: fica parado, mira com um laser (aviso) e atira em Marco. */
export class Pistoleiro extends Inimigo {
  private estado: Estado = 'vigiando';
  private readonly laser: Phaser.GameObjects.Graphics;

  constructor(scene: Phaser.Scene, x: number, y: number) {
    super(scene, x, y, 'pistoleiro');
    this.laser = scene.add.graphics().setDepth(5).setBlendMode(Phaser.BlendModes.ADD);
    this.animar('parado');
  }

  private cano(): { x: number; y: number } {
    return { x: this.x + this.direcao * CANO.x, y: this.y + CANO.y };
  }

  pensar(mundo: Mundo): void {
    if (!this.vivo) return;
    this.corpo.setVelocityX(0);

    if (this.estado === 'vigiando' && this.veMarco(mundo, VISAO, ALTURA_VISAO)) {
      this.mirar(mundo);
    }

    if (this.estado === 'mirando') {
      this.direcao = Math.sign(mundo.marco.x - this.x) || this.direcao;
      this.olhar();
      const c = this.cano();
      this.laser.clear();
      this.laser.lineStyle(1, 0xff2a6d, 0.9);
      this.laser.lineBetween(c.x, c.y, mundo.marco.x, mundo.marco.y);
      this.laser.fillStyle(0xff2a6d, 0.8).fillCircle(mundo.marco.x, mundo.marco.y, 1.5);
    }
  }

  override morrer(direcaoGolpe: number): void {
    this.laser.clear();
    super.morrer(direcaoGolpe);
  }

  override destroy(fromScene?: boolean): void {
    this.laser.destroy();
    super.destroy(fromScene);
  }

  private mirar(mundo: Mundo): void {
    this.estado = 'mirando';
    this.animar('mirar');

    this.depois(MIRA_MS, () => {
      this.laser.clear();
      if (mundo.marcoVivo() && mundo.temVisao(this, mundo.marco)) {
        const c = this.cano();
        const angulo = Phaser.Math.Angle.Between(c.x, c.y, mundo.marco.x, mundo.marco.y);
        mundo.dispararBala(c.x, c.y, angulo);
        this.animar('atirar');
      }
      this.estado = 'recarga';
      this.depois(RECARGA_MS, () => {
        this.estado = 'vigiando';
        this.animar('parado');
      });
    });
  }
}
