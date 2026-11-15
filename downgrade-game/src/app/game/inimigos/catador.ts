import Phaser from 'phaser';
import { Inimigo, Mundo } from './inimigo';

const VEL_PATRULHA = 55;
const VEL_PERSEGUIR = 170;
const VISAO = 210;
const ALCANCE_GOLPE = 40;
const PREPARO_MS = 290; // levanta o cano e pisca (telegrafa)
const RECUPERACAO_MS = 420;

type Estado = 'patrulha' | 'perseguir' | 'preparando' | 'recuperando';

/** Catador do Rato: patrulha, persegue quando ve Marco e ataca de perto com um cano. */
export class Catador extends Inimigo {
  private estado: Estado = 'patrulha';
  private readonly origemX: number;

  constructor(scene: Phaser.Scene, x: number, y: number, private readonly raioPatrulha = 80) {
    super(scene, x, y, 'catador');
    this.origemX = x;
    this.animar('andar');
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
        this.animar('andar');
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
          this.animar('correr');
        }
        break;

      default:
        this.corpo.setVelocityX(0);
    }
    this.olhar();
  }

  private preparar(mundo: Mundo): void {
    this.estado = 'preparando';
    this.corpo.setVelocityX(0);
    this.animar('preparar');
    this.depois(PREPARO_MS - 100, () => this.piscar(100));

    this.depois(PREPARO_MS, () => {
      this.animar('golpe');
      const dx = mundo.marco.x - this.x;
      const dy = mundo.marco.y - this.y;
      const naFrente = Math.sign(dx) === this.direcao || Math.abs(dx) < 6;
      if (mundo.marcoVivo() && naFrente && Math.abs(dx) <= ALCANCE_GOLPE + 10 && Math.abs(dy) < 40) {
        mundo.matarMarco('UM CATADOR TE ACERTOU.');
      }
      this.estado = 'recuperando';
      this.depois(RECUPERACAO_MS, () => (this.estado = 'perseguir'));
    });
  }
}
