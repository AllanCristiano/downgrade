import Phaser from 'phaser';
import { Escama } from '../escama/escama';

const W = 960;
const H = 540;
const VELOCIDADE = 280;
const PULO = 560;
const FATOR_OVERTIME = 3;
const VIDA_MAX = 100;

/** Em desenvolvimento libera Canhao e Overtime para testar. Na campanha eles vem da historia. */
const DEV_LIBERAR_TUDO = true;

type Teclas = Record<'W' | 'A' | 'D' | 'J' | 'K' | 'R' | 'SPACE' | 'SHIFT', Phaser.Input.Keyboard.Key>;

/** Fase 1 — O Lixão (prototipo). Marco acabou de acordar a Escama Zero. */
export class LixaoScene extends Phaser.Scene {
  private escama!: Escama;
  private marco!: Phaser.GameObjects.Rectangle;
  private corpo!: Phaser.Physics.Arcade.Body;
  private corte!: Phaser.GameObjects.Rectangle;
  private corteCorpo!: Phaser.Physics.Arcade.Body;
  private tiros!: Phaser.Physics.Arcade.Group;
  private inimigos!: Phaser.Physics.Arcade.StaticGroup;
  private filtroOvertime!: Phaser.GameObjects.Rectangle;
  private barraVida!: Phaser.GameObjects.Graphics;
  private hud!: Phaser.GameObjects.Text;
  private teclas!: Teclas;

  private vida = VIDA_MAX;
  private direcao = 1;
  private atacando = false;
  private ultimoTiro = 0;
  private morto = false;

  constructor() {
    super('lixao');
  }

  create(): void {
    this.escama = new Escama();
    if (DEV_LIBERAR_TUDO) {
      this.escama.absorver('canhao');
      this.escama.absorver('overtime');
    }
    this.vida = VIDA_MAX;
    this.direcao = 1;
    this.atacando = false;
    this.morto = false;

    // Pilhas de sucata
    const solidos = this.physics.add.staticGroup();
    solidos.add(this.add.rectangle(W / 2, H - 20, W, 40, 0x2a1b3d));
    solidos.add(this.add.rectangle(300, 380, 200, 16, 0x3d2a5c));
    solidos.add(this.add.rectangle(680, 290, 220, 16, 0x3d2a5c));

    // Marco
    this.marco = this.add.rectangle(80, H - 80, 22, 40, 0x00f0ff);
    this.physics.add.existing(this.marco);
    this.corpo = this.marco.body as Phaser.Physics.Arcade.Body;
    this.corpo.setCollideWorldBounds(true);
    this.physics.add.collider(this.marco, solidos);

    // Catadores com Escamas piratas
    this.inimigos = this.physics.add.staticGroup();
    for (const [x, y] of [[300, 352], [680, 262], [880, 500], [520, 500]]) {
      this.inimigos.add(this.add.rectangle(x, y, 22, 40, 0xff2a6d));
    }

    // Espada
    this.corte = this.add.rectangle(0, 0, this.escama.alcanceEspada(), 34, 0xffffff, 0.6).setVisible(false);
    this.physics.add.existing(this.corte);
    this.corteCorpo = this.corte.body as Phaser.Physics.Arcade.Body;
    this.corteCorpo.setAllowGravity(false);
    this.corteCorpo.enable = false;
    this.physics.add.overlap(this.corte, this.inimigos, (_c, inimigo) => this.matar(inimigo as Phaser.GameObjects.Rectangle));

    // Canhao
    this.tiros = this.physics.add.group({ allowGravity: false });
    this.physics.add.overlap(this.tiros, this.inimigos, (_t, inimigo) => this.matar(inimigo as Phaser.GameObjects.Rectangle));
    this.physics.add.collider(this.tiros, solidos, (tiro) => (tiro as Phaser.GameObjects.Rectangle).destroy());

    // HUD
    this.filtroOvertime = this.add.rectangle(W / 2, H / 2, W, H, 0x6a00ff, 0).setDepth(10);
    this.barraVida = this.add.graphics().setDepth(11);
    this.hud = this.add.text(16, 34, '', { fontFamily: 'Courier New', fontSize: '15px', color: '#e8e6ff' }).setDepth(11);

    this.teclas = this.input.keyboard!.addKeys('W,A,D,J,K,R,SPACE,SHIFT') as Teclas;
    this.input.on('pointerdown', () => this.atacar());
  }

  override update(_time: number, delta: number): void {
    const t = this.teclas;

    if (Phaser.Input.Keyboard.JustDown(t.R)) {
      this.definirOvertime(false);
      this.scene.restart();
      return;
    }
    if (this.morto) return;

    // Overtime: camera lenta que drena vida (delta e tempo real, nao e afetado pela camera lenta)
    const overtime = this.escama.tem('overtime') && t.SHIFT.isDown && this.vida > 0;
    this.definirOvertime(overtime);
    if (overtime) {
      this.vida = Math.max(0, this.vida - this.escama.drenoOvertime() * (delta / 1000));
      if (this.vida <= 0) return this.morrer('A Escama consumiu Marco. Overtime demais.');
    }

    // Movimento
    let vx = 0;
    if (t.A.isDown) vx -= VELOCIDADE;
    if (t.D.isDown) vx += VELOCIDADE;
    if (vx !== 0) this.direcao = Math.sign(vx);
    this.corpo.setVelocityX(vx);

    if ((Phaser.Input.Keyboard.JustDown(t.W) || Phaser.Input.Keyboard.JustDown(t.SPACE)) && this.corpo.blocked.down) {
      this.corpo.setVelocityY(-PULO);
    }

    if (Phaser.Input.Keyboard.JustDown(t.J)) this.atacar();
    if (Phaser.Input.Keyboard.JustDown(t.K)) this.atirar();

    if (this.atacando) {
      this.corte.setPosition(this.marco.x + this.direcao * (this.escama.alcanceEspada() / 2 + 11), this.marco.y);
      this.corteCorpo.reset(this.corte.x, this.corte.y);
    }

    this.desenharHud(overtime);
  }

  private atacar(): void {
    if (this.atacando || this.morto) return;
    this.atacando = true;
    this.corte.setVisible(true);
    this.corteCorpo.enable = true;
    this.time.delayedCall(120, () => {
      this.atacando = false;
      this.corte.setVisible(false);
      this.corteCorpo.enable = false;
    });
  }

  private atirar(): void {
    if (!this.escama.tem('canhao') || this.morto) return;
    if (this.time.now - this.ultimoTiro < this.escama.recargaCanhao()) return;
    this.ultimoTiro = this.time.now;

    const tiro = this.add.rectangle(this.marco.x + this.direcao * 16, this.marco.y - 4, 14, 4, 0xffd166);
    this.tiros.add(tiro);
    (tiro.body as Phaser.Physics.Arcade.Body).setVelocityX(this.direcao * 900);
    this.time.delayedCall(1200, () => tiro.destroy());
  }

  private matar(inimigo: Phaser.GameObjects.Rectangle): void {
    this.cameras.main.shake(80, 0.006);
    inimigo.destroy();
  }

  private morrer(msg: string): void {
    this.morto = true;
    this.definirOvertime(false);
    this.corpo.setVelocity(0, 0);
    this.marco.setFillStyle(0x555555);
    this.add.text(W / 2, H / 2, `${msg}\nR para tentar de novo`, {
      fontFamily: 'Courier New', fontSize: '22px', color: '#ff2a6d', align: 'center',
    }).setOrigin(0.5).setDepth(12);
    this.desenharHud(false);
  }

  private definirOvertime(ativo: boolean): void {
    this.physics.world.timeScale = ativo ? FATOR_OVERTIME : 1;
    this.time.timeScale = ativo ? 1 / FATOR_OVERTIME : 1;
    this.filtroOvertime.setFillStyle(0x6a00ff, ativo ? 0.18 : 0);
  }

  private desenharHud(overtime: boolean): void {
    const g = this.barraVida;
    g.clear();
    g.fillStyle(0x2a1b3d).fillRect(16, 14, 200, 12);
    g.fillStyle(overtime ? 0xb388ff : 0x3dff9a).fillRect(16, 14, 200 * (this.vida / VIDA_MAX), 12);

    const restantes = this.inimigos.countActive();
    const hab = this.escama.habilidades;
    this.hud.setText(
      (restantes > 0 ? `Inimigos: ${restantes}` : 'LIXÃO LIMPO! R para reiniciar') +
      `\nEspada nv${hab.espada.nivel}` +
      (hab.canhao.desbloqueada ? ` · Canhão nv${hab.canhao.nivel}` : '') +
      (hab.overtime.desbloqueada ? ` · Overtime nv${hab.overtime.nivel}` : ''),
    );
  }
}
