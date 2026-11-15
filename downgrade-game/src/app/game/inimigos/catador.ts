import Phaser from 'phaser';
import { Inimigo, Mundo } from './inimigo';

const VEL_PATRULHA = 55;
const VEL_PERSEGUIR = 170;
const ACEL = 700; // px/s²: arranca e freia com peso
const VISAO = 210;
const ALCANCE_GOLPE = 40;
const PAUSA_PATRULHA_MS = 650; // para, "olha em volta" e so entao vira
const PREPARO_MS = 290; // levanta o cano e pisca (telegrafa)
const RECUPERACAO_MS = 420;

type Estado = 'patrulha' | 'pausa' | 'perseguir' | 'preparando' | 'recuperando';

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

    if ((this.estado === 'patrulha' || this.estado === 'pausa') && this.veMarco(mundo, VISAO, 50)) {
      this.estado = 'perseguir';
    }

    switch (this.estado) {
      case 'patrulha': {
        const passou = (this.direcao > 0 && this.x > this.origemX + this.raioPatrulha) ||
          (this.direcao < 0 && this.x < this.origemX - this.raioPatrulha) ||
          (this.direcao > 0 && this.corpo.blocked.right) || (this.direcao < 0 && this.corpo.blocked.left);
        if (passou) {
          this.estado = 'pausa';
          this.depois(PAUSA_PATRULHA_MS, () => {
            if (this.estado !== 'pausa') return;
            this.direcao = -this.direcao;
            this.estado = 'patrulha';
          });
          break;
        }
        this.acelerar(this.direcao * VEL_PATRULHA, ACEL);
        this.animar('andar');
        break;
      }

      case 'pausa':
        this.acelerar(0, ACEL);
        if (Math.abs(this.corpo.velocity.x) < 20) this.animar('parado');
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
          this.acelerar(this.direcao * VEL_PERSEGUIR, ACEL * 1.6);
          this.animar(Math.abs(this.corpo.velocity.x) > 90 ? 'correr' : 'andar');
          this.anims.timeScale = 0.6 + 0.6 * Math.abs(this.corpo.velocity.x) / VEL_PERSEGUIR;
        }
        break;

      default:
        this.acelerar(0, ACEL * 2);
    }
    if (this.estado !== 'perseguir') this.anims.timeScale = 1;
    this.olhar();
  }

  private preparar(mundo: Mundo): void {
    this.estado = 'preparando';
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
