import Phaser from 'phaser';
import { Inimigo, Mundo } from './inimigo';

const VISAO = 480;
const ALTURA_VISAO = 160;
const MIRA_MS = 650; // laser de mira visivel antes do tiro
const RECARGA_MS = 1100;

type Estado = 'vigiando' | 'mirando' | 'recarga';

/** Pistoleiro: fica parado, mira com um laser (aviso) e atira em Marco. */
export class Pistoleiro extends Inimigo {
  private estado: Estado = 'vigiando';
  private readonly laser: Phaser.GameObjects.Graphics;

  constructor(scene: Phaser.Scene, x: number, y: number) {
    super(scene, x, y, 0xff8c42);
    this.laser = scene.add.graphics().setDepth(5);
  }

  pensar(mundo: Mundo): void {
    if (!this.vivo) return;
    this.corpo.setVelocityX(0);

    if (this.estado === 'vigiando' && this.veMarco(mundo, VISAO, ALTURA_VISAO)) {
      this.mirar(mundo);
    }

    if (this.estado === 'mirando') {
      this.direcao = Math.sign(mundo.marco.x - this.x) || this.direcao;
      this.laser.clear();
      this.laser.lineStyle(1, 0xff2a6d, 0.85);
      this.laser.lineBetween(this.x, this.y - 6, mundo.marco.x, mundo.marco.y);
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
    this.depois(MIRA_MS, () => {
      this.laser.clear();
      if (mundo.marcoVivo() && mundo.temVisao(this, mundo.marco)) {
        const angulo = Phaser.Math.Angle.Between(this.x, this.y - 6, mundo.marco.x, mundo.marco.y);
        mundo.dispararBala(this.x + Math.cos(angulo) * 18, this.y - 6 + Math.sin(angulo) * 18, angulo);
      }
      this.estado = 'recarga';
      this.depois(RECARGA_MS, () => (this.estado = 'vigiando'));
    });
  }
}
