import Phaser from 'phaser';
import { Inimigo, Mundo } from './inimigo';

const VEL_PATRULHA = 60;
const VEL_PERSEGUIR = 175;
const VISAO = 260;
const ALCANCE_GOLPE = 40;
const PREPARO_MS = 280; // telegrafa o golpe (pisca branco)
const RECUPERACAO_MS = 450;

type Estado = 'patrulha' | 'perseguir' | 'preparando' | 'recuperando';

/** Catador do Rato: patrulha, persegue quando ve Marco e ataca de perto. */
export class Catador extends Inimigo {
  private estado: Estado = 'patrulha';
  private readonly origemX: number;

  constructor(scene: Phaser.Scene, x: number, y: number, private readonly raioPatrulha = 80) {
    super(scene, x, y, 0xff2a6d);
    this.origemX = x;
  }

  pensar(mundo: Mundo): void {
    if (!this.vivo) return;
    const dx = mundo.marco.x - this.x;
    const dy = mundo.marco.y - this.y;

    switch (this.estado) {
      case 'patrulha':
        if (this.x > this.origemX + this.raioPatrulha || this.corpo.blocked.right) this.direcao = -1;
        if (this.x < this.origemX - this.raioPatrulha || this.corpo.blocked.left) this.direcao = 1;
        this.corpo.setVelocityX(this.direcao * VEL_PATRULHA);
        if (this.veMarco(mundo, VISAO, 50)) this.estado = 'perseguir';
        break;

      case 'perseguir':
        if (!mundo.marcoVivo()) {
          this.estado = 'patrulha';
          break;
        }
        this.direcao = Math.sign(dx) || this.direcao;
        if (Math.abs(dx) <= ALCANCE_GOLPE && Math.abs(dy) < 40) {
          this.preparar(mundo);
        } else {
          this.corpo.setVelocityX(this.direcao * VEL_PERSEGUIR);
        }
        break;

      default:
        this.corpo.setVelocityX(0);
    }
  }

  private preparar(mundo: Mundo): void {
    this.estado = 'preparando';
    this.corpo.setVelocityX(0);
    this.setFillStyle(0xffffff);

    this.depois(PREPARO_MS, () => {
      this.setFillStyle(this.cor);
      const golpe = this.scene.add.rectangle(this.x + this.direcao * 26, this.y, 34, 22, 0xff2a6d, 0.6);
      this.scene.time.delayedCall(90, () => golpe.destroy());

      const dx = mundo.marco.x - this.x;
      const dy = mundo.marco.y - this.y;
      const naFrente = Math.sign(dx) === this.direcao || Math.abs(dx) < 6;
      if (mundo.marcoVivo() && naFrente && Math.abs(dx) <= ALCANCE_GOLPE + 10 && Math.abs(dy) < 40) {
        mundo.matarMarco('Um Catador te pegou.');
      }

      this.estado = 'recuperando';
      this.depois(RECUPERACAO_MS, () => (this.estado = 'perseguir'));
    });
  }
}
