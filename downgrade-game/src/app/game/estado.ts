import Phaser from 'phaser';
import { Escama } from './escama/escama';
import { InfoFase } from './fases/fases';

/** Zoom da camera do mundo: a arte e desenhada em 1x e exibida em 2x (pixel art grande e nitida). */
export const ZOOM = 2;
export const TELA_W = 960;
export const TELA_H = 540;

export type Arma = 'espada' | 'canhao';

/** O que a cena da fase expoe para as cenas de fundo e HUD (lidas a cada frame). */
export interface EstadoFase {
  readonly info?: InfoFase;
  readonly inicioId: number; // muda a cada (re)inicio da fase
  readonly escama?: Escama;
  readonly vida: number;
  readonly vidaMax: number;
  readonly tempoMs: number;
  readonly mortes: number;
  readonly restantes: number;
  readonly arma: Arma;
  readonly overtime: boolean;
  readonly morto: boolean;
  readonly motivoMorte: string;
  readonly concluida: boolean;
  readonly cameras: Phaser.Cameras.Scene2D.CameraManager;
}

/** Filtro de cor do Overtime + bloom, aplicado nas cameras (somente WebGL). */
export class EfeitosCamera {
  private matriz?: Phaser.FX.ColorMatrix;

  constructor(scene: Phaser.Scene, cam: Phaser.Cameras.Scene2D.Camera, bloom = true) {
    if (scene.game.renderer.type !== Phaser.WEBGL) return;
    if (bloom) cam.postFX.addBloom(0xffffff, 1, 1, 0.9, 1.15, 4);
    this.matriz = cam.postFX.addColorMatrix();
  }

  overtime(ativo: boolean): void {
    if (!this.matriz) return;
    this.matriz.reset();
    if (ativo) {
      this.matriz.saturate(-0.55);
      this.matriz.hue(-25, true);
      this.matriz.contrast(0.15, true);
    }
  }
}
