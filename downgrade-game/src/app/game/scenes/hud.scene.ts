import Phaser from 'phaser';
import { EstadoFase, TELA_H, TELA_W } from '../estado';

const FONTE = 'Courier New, monospace';
const SEGMENTOS = 20;

/** HUD por cima de tudo (sem zoom): vida da Escama, armas, tempo, chuva e mensagens. */
export class HudScene extends Phaser.Scene {
  private g!: Phaser.GameObjects.Graphics;
  private tempo!: Phaser.GameObjects.Text;
  private info!: Phaser.GameObjects.Text;
  private armas!: Phaser.GameObjects.Text;
  private mensagem!: Phaser.GameObjects.Text;
  private banner!: Phaser.GameObjects.Text;
  private avisoOvertime!: Phaser.GameObjects.Text;
  private vinheta!: Phaser.GameObjects.Rectangle;
  private chuva?: Phaser.GameObjects.Particles.ParticleEmitter;
  private inicioVisto = -1;

  constructor() {
    super('hud');
  }

  create(): void {
    this.criarChuva();
    this.vinheta = this.add.rectangle(TELA_W / 2, TELA_H / 2, TELA_W, TELA_H, 0x5a00c8, 0);
    this.g = this.add.graphics();
    const estilo = { fontFamily: FONTE, fontStyle: 'bold', color: '#e8e6ff' };
    this.add.text(20, 14, 'ESCAMA', { ...estilo, fontSize: '13px', color: '#00f0ff' }).setLetterSpacing(3);
    this.armas = this.add.text(20, 50, '', { ...estilo, fontSize: '14px' });
    this.tempo = this.add.text(TELA_W - 20, 12, '', { ...estilo, fontSize: '26px' }).setOrigin(1, 0);
    this.info = this.add.text(TELA_W - 20, 44, '', { ...estilo, fontSize: '13px', color: '#b8a8e0' }).setOrigin(1, 0);
    this.mensagem = this.add.text(TELA_W / 2, TELA_H / 2, '', {
      ...estilo, fontSize: '24px', color: '#ff2a6d', align: 'center', stroke: '#07010f', strokeThickness: 6,
    }).setOrigin(0.5);
    this.banner = this.add.text(TELA_W / 2, TELA_H * 0.28, '', {
      ...estilo, fontSize: '30px', color: '#00f0ff', align: 'center', stroke: '#07010f', strokeThickness: 6,
    }).setOrigin(0.5).setAlpha(0);
    this.avisoOvertime = this.add.text(TELA_W / 2, TELA_H - 40, 'O V E R T I M E', {
      ...estilo, fontSize: '18px', color: '#c9a0ff', stroke: '#07010f', strokeThickness: 4,
    }).setOrigin(0.5).setVisible(false);
  }

  private criarChuva(): void {
    if (!this.textures.exists('gota')) {
      const g = this.make.graphics({}, false);
      g.fillStyle(0xb8a8e0, 1).fillRect(0, 0, 2, 14);
      g.generateTexture('gota', 2, 14);
      g.destroy();
    }
    this.chuva = this.add.particles(0, 0, 'gota', {
      x: { min: -80, max: TELA_W + 300 },
      y: -20,
      lifespan: 900,
      speedY: { min: 900, max: 1150 },
      speedX: { min: -240, max: -190 },
      rotate: 12,
      alpha: { min: 0.1, max: 0.32 },
      quantity: 2,
      frequency: 12,
    });
  }

  override update(time: number): void {
    const f = this.scene.get('fase') as unknown as EstadoFase;
    if (!f.info) return;

    if (f.inicioId !== this.inicioVisto) {
      this.inicioVisto = f.inicioId;
      if (f.mortes === 0) this.mostrarBanner(`FASE ${f.info.numero}\n${f.info.nome.toUpperCase()}`);
    }

    // Overtime
    const ot = f.overtime;
    this.vinheta.setFillStyle(0x5a00c8, ot ? 0.12 : 0);
    this.avisoOvertime.setVisible(ot).setAlpha(0.6 + 0.4 * Math.sin(time / 90));
    if (this.chuva) this.chuva.timeScale = ot ? 1 / 3 : 1;

    // Vida (segmentos)
    const g = this.g;
    g.clear();
    const x0 = 20, y0 = 30, segW = 11, segH = 12;
    const cheios = Math.ceil((f.vida / f.vidaMax) * SEGMENTOS);
    g.fillStyle(0x07010f, 0.75).fillRect(x0 - 4, y0 - 4, SEGMENTOS * (segW + 2) + 6, segH + 8);
    for (let i = 0; i < SEGMENTOS; i++) {
      const cor = i < cheios ? (ot ? 0xb388ff : i < 4 ? 0xff2a6d : 0x3dff9a) : 0x2a1b3d;
      g.fillStyle(cor, 1).fillRect(x0 + i * (segW + 2), y0, segW, segH);
      if (i < cheios) g.fillStyle(0xffffff, 0.35).fillRect(x0 + i * (segW + 2), y0, segW, 2);
    }

    // Armas
    const h = f.escama?.habilidades;
    if (h) {
      const espada = `${f.arma === 'espada' ? '▶' : ' '} ESPADA nv${h.espada.nivel}`;
      const canhao = h.canhao.desbloqueada ? `   ${f.arma === 'canhao' ? '▶' : ' '} CANHÃO nv${h.canhao.nivel}  [Q]` : '';
      const overtime = h.overtime.desbloqueada ? `\n  OVERTIME nv${h.overtime.nivel}  [SHIFT]` : '';
      this.armas.setText(espada + canhao + overtime);
    }

    // Tempo e contadores
    const s = f.tempoMs / 1000;
    this.tempo.setText(`${Math.floor(s / 60)}:${(s % 60).toFixed(2).padStart(5, '0')}`);
    this.info.setText(`☠ ${f.mortes}    INIMIGOS ${f.restantes}`);

    // Mensagens
    this.mensagem.setText(f.morto ? `${f.motivoMorte}\n\nR · J · CLIQUE para tentar de novo` : '');
    if (f.restantes === 0 && !f.concluida && !f.morto) {
      this.info.setText(`☠ ${f.mortes}    SAÍDA ABERTA →`).setColor('#3dff9a');
    } else {
      this.info.setColor('#b8a8e0');
    }
  }

  private mostrarBanner(texto: string): void {
    this.tweens.killTweensOf(this.banner);
    this.banner.setText(texto).setAlpha(0).setScale(1.15);
    this.tweens.chain({
      targets: this.banner,
      tweens: [
        { alpha: 1, scale: 1, duration: 350, ease: 'Cubic.easeOut' },
        { alpha: 1, duration: 1300 },
        { alpha: 0, duration: 500 },
      ],
    });
  }
}
