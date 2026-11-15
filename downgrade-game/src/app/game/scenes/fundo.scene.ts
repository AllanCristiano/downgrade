import Phaser from 'phaser';
import { EfeitosCamera, EstadoFase, TELA_H, TELA_W, ZOOM } from '../estado';

/**
 * Camadas de fundo com parallax, desenhadas atras da fase.
 * A arte dos fundos tem 480x272 e e exibida em 2x (mesmo tamanho de pixel do mundo).
 */
export class FundoScene extends Phaser.Scene {
  private camadas: { img: Phaser.GameObjects.TileSprite; fator: number }[] = [];
  private faseMontada = -1;
  private efeitos?: EfeitosCamera;

  constructor() {
    super('fundo');
  }

  create(): void {
    this.efeitos = new EfeitosCamera(this, this.cameras.main);
  }

  override update(): void {
    const fase = this.scene.get('fase') as unknown as EstadoFase;
    const info = fase.info;
    if (!info) return;

    if (info.numero !== this.faseMontada) {
      const urls = (info.fundos ?? []).map((f) => f.url);
      if (!urls.every((u) => this.textures.exists(u))) return; // a fase ainda esta carregando
      this.camadas.forEach((c) => c.img.destroy());
      this.camadas = (info.fundos ?? []).map((f) => ({
        img: this.add.tileSprite(0, 0, TELA_W, TELA_H + 8, f.url).setOrigin(0).setTileScale(ZOOM),
        fator: f.fator,
      }));
      this.faseMontada = info.numero;
    }

    const cam = fase.cameras.main;
    const maxY = Math.max(0, cam.getBounds().height - cam.height / cam.zoom);
    for (const c of this.camadas) {
      c.img.tilePositionX = cam.scrollX * c.fator;
      // quando a camera sobe, as camadas proximas descem um pouco (parallax vertical)
      c.img.y = (maxY - cam.scrollY) * c.fator * ZOOM * 0.5;
    }
    this.efeitos?.overtime(fase.overtime);
  }
}
