import Phaser from 'phaser';
import { Escama } from '../escama/escama';
import { EVENTO_FASE_COMPLETA, ResultadoFase } from '../eventos';
import { Inimigo, Mundo } from '../inimigos/inimigo';
import { Catador } from '../inimigos/catador';
import { Pistoleiro } from '../inimigos/pistoleiro';

const TELA_W = 960;
const TELA_H = 540;
const MUNDO_W = 1920;
const VELOCIDADE = 280;
const PULO = 560;
const FATOR_OVERTIME = 3;
const VIDA_MAX = 100;
const VEL_BALA = 520;

const FASE = 1;
const NOME_FASE = 'Fase 1 — O Lixão';

// Chaves no registry do jogo: sobrevivem ao restart da cena (tempo e mortes da tentativa)
const REG_INICIO = 'fase.inicio';
const REG_MORTES = 'fase.mortes';

/**
 * Em desenvolvimento: Espada nv 2 (rebate balas) e Canhao/Overtime liberados para teste.
 * Na campanha, a fase 1 comeca so com Espada nv 0.
 */
const DEV_LIBERAR_TUDO = true;

type Teclas = Record<'W' | 'A' | 'D' | 'J' | 'Q' | 'R' | 'SPACE' | 'SHIFT', Phaser.Input.Keyboard.Key>;
type Ret = Phaser.GameObjects.Rectangle;
type Arma = 'espada' | 'canhao';

/** Fase 1 — O Lixão. Marco acabou de acordar a Escama e os Catadores do Rato vieram atrás. */
export class LixaoScene extends Phaser.Scene implements Mundo {
  marco!: Ret;
  private escama!: Escama;
  private corpo!: Phaser.Physics.Arcade.Body;
  private corte!: Ret; // hitbox (invisivel)
  private corteCorpo!: Phaser.Physics.Arcade.Body;
  private lamina!: Ret; // visual do corte, rotacionado para o mouse
  private mira!: Phaser.GameObjects.Graphics;
  private solidos!: Phaser.Physics.Arcade.StaticGroup;
  private bordasSolidos: Phaser.Geom.Rectangle[] = [];
  private inimigos!: Phaser.Physics.Arcade.Group;
  private balas!: Phaser.Physics.Arcade.Group;
  private tirosMarco!: Phaser.Physics.Arcade.Group;
  private saida!: Ret;
  private filtroOvertime!: Ret;
  private barraVida!: Phaser.GameObjects.Graphics;
  private hud!: Phaser.GameObjects.Text;
  private teclas!: Teclas;

  private vida = VIDA_MAX;
  private direcao = 1;
  private arma: Arma = 'espada';
  private anguloCorte = 0;
  private atacando = false;
  private ultimoTiro = 0;
  private morto = false;
  private concluida = false;

  constructor() {
    super('lixao');
  }

  // ------------------------------------------------------------------ setup

  create(): void {
    this.prepararEscama();
    this.vida = VIDA_MAX;
    this.direcao = 1;
    this.arma = 'espada';
    this.atacando = false;
    this.morto = false;
    this.concluida = false;

    if (this.registry.get(REG_INICIO) === undefined) {
      this.registry.set(REG_INICIO, performance.now());
      this.registry.set(REG_MORTES, 0);
    }

    this.physics.world.setBounds(0, 0, MUNDO_W, TELA_H);
    this.cameras.main.setBounds(0, 0, MUNDO_W, TELA_H);

    this.criarCenario();
    this.criarMarco();
    this.criarInimigos();
    this.criarArmas();
    this.criarHud();

    this.cameras.main.startFollow(this.marco, true, 0.12, 0.12);

    this.input.keyboard!.enableGlobalCapture();
    this.teclas = this.input.keyboard!.addKeys('W,A,D,J,Q,R,SPACE,SHIFT') as Teclas;
    this.input.setDefaultCursor('none');
    this.input.on('pointerdown', (p: Phaser.Input.Pointer) => {
      if (!p.leftButtonDown()) return;
      if (this.morto) this.tentarDeNovo();
      else this.atacar();
    });
  }

  private prepararEscama(): void {
    this.escama = new Escama();
    if (DEV_LIBERAR_TUDO) {
      this.escama.fragmentos = 2;
      this.escama.upar('espada');
      this.escama.upar('espada');
      this.escama.absorver('canhao');
      this.escama.absorver('overtime');
    }
  }

  private criarCenario(): void {
    // Montes de sucata do Aterro 9
    const blocos: [number, number, number, number][] = [
      [MUNDO_W / 2, TELA_H - 20, MUNDO_W, 40], // chao
      [300, 380, 200, 16],
      [640, 300, 180, 16],
      [900, 400, 160, 16],
      [1150, 455, 60, 90], // pilha de sucata (pular por cima)
      [1400, 360, 200, 16],
      [1700, 280, 160, 16],
    ];
    this.solidos = this.physics.add.staticGroup();
    this.bordasSolidos = [];
    for (const [x, y, w, h] of blocos) {
      const r = this.add.rectangle(x, y, w, h, h > 20 ? 0x2a1b3d : 0x3d2a5c);
      this.solidos.add(r);
      this.bordasSolidos.push(r.getBounds());
    }

    // Saida: so abre com o lixao limpo
    this.saida = this.add.rectangle(MUNDO_W - 30, TELA_H - 80, 30, 80, 0x1b3d2a).setStrokeStyle(2, 0x3dff9a, 0.3);
  }

  private criarMarco(): void {
    this.marco = this.add.rectangle(60, TELA_H - 60, 22, 40, 0x00f0ff).setDepth(2);
    this.physics.add.existing(this.marco);
    this.corpo = this.marco.body as Phaser.Physics.Arcade.Body;
    this.corpo.setCollideWorldBounds(true);
    this.physics.add.collider(this.marco, this.solidos);
  }

  private criarInimigos(): void {
    this.inimigos = this.physics.add.group({ collideWorldBounds: true });
    const chao = TELA_H - 60;
    const lista: Inimigo[] = [
      new Catador(this, 520, chao, 80),
      new Pistoleiro(this, 300, 352),
      new Catador(this, 900, 372, 50),
      new Catador(this, 1300, chao, 100),
      new Pistoleiro(this, 1400, 332),
      new Catador(this, 1620, chao, 80),
      new Pistoleiro(this, 1700, 252),
    ];
    for (const i of lista) this.inimigos.add(i);
    this.physics.add.collider(this.inimigos, this.solidos);
  }

  private criarArmas(): void {
    // Espada: hitbox quadrada (Arcade nao rotaciona corpos) + lamina visual rotacionada
    const tamHitbox = this.escama.alcanceEspada() * 0.8;
    this.corte = this.add.rectangle(0, 0, tamHitbox, tamHitbox).setVisible(false);
    this.lamina = this.add.rectangle(0, 0, this.escama.alcanceEspada(), 10, 0xffffff, 0.8).setVisible(false).setDepth(3);
    this.physics.add.existing(this.corte);
    this.corteCorpo = this.corte.body as Phaser.Physics.Arcade.Body;
    this.corteCorpo.setAllowGravity(false);
    this.corteCorpo.enable = false;

    this.balas = this.physics.add.group({ allowGravity: false });
    this.tirosMarco = this.physics.add.group({ allowGravity: false });

    // Espada mata inimigos (corpo voa na direcao horizontal do corte)
    this.physics.add.overlap(this.corte, this.inimigos, (a, b) =>
      this.acertar(this.comoInimigo(a, b), Math.sign(Math.cos(this.anguloCorte)) || 1));

    // Espada nv 2+ rebate balas
    this.physics.add.overlap(this.corte, this.balas, (a, b) => this.rebater(this.comoBala(a, b)));

    // Bala inimiga mata Marco; bala rebatida mata inimigo
    this.physics.add.overlap(this.marco, this.balas, (a, b) => {
      const bala = this.comoBala(a, b);
      if (!bala.getData('rebatida')) {
        bala.destroy();
        this.matarMarco('Levou um tiro.');
      }
    });
    this.physics.add.overlap(this.balas, this.inimigos, (a, b) => {
      const bala = this.comoBala(a, b);
      if (!bala.getData('rebatida')) return;
      const inimigo = this.comoInimigo(a, b);
      this.acertar(inimigo, Math.sign(bala.body!.velocity.x) || 1);
      bala.destroy();
    });

    // Canhao de Marco
    this.physics.add.overlap(this.tirosMarco, this.inimigos, (a, b) => {
      const tiro = this.comoBala(a, b);
      this.acertar(this.comoInimigo(a, b), Math.sign(tiro.body!.velocity.x) || 1);
    });

    // Tudo que voa morre na parede
    this.physics.add.collider(this.balas, this.solidos, (a, b) => this.comoBala(a, b).destroy());
    this.physics.add.collider(this.tirosMarco, this.solidos, (a, b) => this.comoBala(a, b).destroy());
  }

  private criarHud(): void {
    this.filtroOvertime = this.add.rectangle(TELA_W / 2, TELA_H / 2, TELA_W, TELA_H, 0x6a00ff, 0)
      .setScrollFactor(0).setDepth(10);
    this.barraVida = this.add.graphics().setScrollFactor(0).setDepth(11);
    this.mira = this.add.graphics().setDepth(12);
    this.hud = this.add.text(16, 34, '', { fontFamily: 'Courier New', fontSize: '15px', color: '#e8e6ff' })
      .setScrollFactor(0).setDepth(11);
  }

  // ------------------------------------------------------------------ loop

  override update(_time: number, delta: number): void {
    const t = this.teclas;
    if (this.concluida) return;

    this.desenharMira();

    if (this.morto) {
      if (Phaser.Input.Keyboard.JustDown(t.R) || Phaser.Input.Keyboard.JustDown(t.J)) this.tentarDeNovo();
      return;
    }
    if (Phaser.Input.Keyboard.JustDown(t.R)) return this.tentarDeNovo();

    // Overtime: camera lenta que drena vida (delta e tempo real)
    const overtime = this.escama.tem('overtime') && t.SHIFT.isDown;
    this.definirOvertime(overtime);
    if (overtime) {
      this.vida = Math.max(0, this.vida - this.escama.drenoOvertime() * (delta / 1000));
      if (this.vida <= 0) return this.matarMarco('A Escama consumiu Marco. Overtime demais.');
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

    if (Phaser.Input.Keyboard.JustDown(t.Q)) this.trocarArma();
    if (Phaser.Input.Keyboard.JustDown(t.J)) this.atacar();
    if (this.atacando) this.posicionarCorte();

    for (const i of this.inimigos.getChildren() as Inimigo[]) i.pensar(this);

    const restantes = this.inimigosVivos();
    this.saida.setFillStyle(restantes === 0 ? 0x3dff9a : 0x1b3d2a, restantes === 0 ? 0.8 : 1);
    if (restantes === 0 && Phaser.Geom.Rectangle.Overlaps(this.marco.getBounds(), this.saida.getBounds())) {
      return this.concluir();
    }

    this.desenharHud(overtime, restantes);
  }

  // ------------------------------------------------------------------ Mundo (usado pelos inimigos)

  marcoVivo(): boolean {
    return !this.morto && !this.concluida;
  }

  temVisao(de: Ret, para: Ret): boolean {
    const linha = new Phaser.Geom.Line(de.x, de.y - 10, para.x, para.y - 10);
    return !this.bordasSolidos.some((r) => Phaser.Geom.Intersects.LineToRectangle(linha, r));
  }

  dispararBala(x: number, y: number, angulo: number): void {
    const bala = this.add.rectangle(x, y, 10, 4, 0xff2a6d).setRotation(angulo).setDepth(4);
    bala.setData('bala', true);
    this.balas.add(bala);
    this.physics.velocityFromRotation(angulo, VEL_BALA, (bala.body as Phaser.Physics.Arcade.Body).velocity);
    this.time.delayedCall(2500, () => bala.destroy());
  }

  matarMarco(motivo: string): void {
    if (this.morto || this.concluida) return;
    this.morto = true;
    this.registry.inc(REG_MORTES, 1);
    this.definirOvertime(false);
    this.corpo.setVelocity(0, 0);
    this.corpo.enable = false;
    this.marco.setFillStyle(0x555555);
    this.cameras.main.shake(160, 0.01);
    this.cameras.main.flash(120, 255, 42, 109);

    this.add.text(TELA_W / 2, TELA_H / 2, `${motivo}\n\nR · J · clique para tentar de novo`, {
      fontFamily: 'Courier New', fontSize: '22px', color: '#ff2a6d', align: 'center',
    }).setOrigin(0.5).setScrollFactor(0).setDepth(12);
    this.desenharHud(false, this.inimigosVivos());
  }

  // ------------------------------------------------------------------ acoes de Marco

  /** Q: alterna Espada <-> Canhao (se o Canhao ja foi absorvido). */
  private trocarArma(): void {
    if (!this.escama.tem('canhao')) return;
    this.arma = this.arma === 'espada' ? 'canhao' : 'espada';
  }

  /** Clique / J: usa a arma atual na direcao do mouse. */
  private atacar(): void {
    if (this.morto || this.concluida) return;
    if (this.arma === 'canhao') return this.atirar();
    if (this.atacando) return;

    this.anguloCorte = this.anguloMira();
    this.direcao = Math.cos(this.anguloCorte) >= 0 ? 1 : -1;
    this.atacando = true;
    this.lamina.setVisible(true);
    this.corteCorpo.enable = true;
    this.posicionarCorte();
    this.time.delayedCall(120, () => {
      this.atacando = false;
      this.lamina.setVisible(false);
      this.corteCorpo.enable = false;
    });
  }

  /** O corte acompanha Marco, mas o angulo fica travado no momento do golpe. */
  private posicionarCorte(): void {
    const dist = this.escama.alcanceEspada() / 2 + 8;
    const x = this.marco.x + Math.cos(this.anguloCorte) * dist;
    const y = this.marco.y + Math.sin(this.anguloCorte) * dist;
    this.corte.setPosition(x, y);
    this.corteCorpo.reset(x, y);
    this.lamina.setPosition(x, y).setRotation(this.anguloCorte);
  }

  private atirar(): void {
    if (!this.escama.tem('canhao')) return;
    if (this.time.now - this.ultimoTiro < this.escama.recargaCanhao()) return;
    this.ultimoTiro = this.time.now;

    const angulo = this.anguloMira();
    this.direcao = Math.cos(angulo) >= 0 ? 1 : -1;
    const tiro = this.add.rectangle(
      this.marco.x + Math.cos(angulo) * 18, this.marco.y - 4 + Math.sin(angulo) * 18, 14, 4, 0xffd166,
    ).setRotation(angulo).setDepth(4);
    tiro.setData('bala', true);
    this.tirosMarco.add(tiro);
    this.physics.velocityFromRotation(angulo, 900, (tiro.body as Phaser.Physics.Arcade.Body).velocity);
    this.time.delayedCall(1200, () => tiro.destroy());
  }

  /** Espada nv 2+: a bala volta na direcao do corte (para onde o mouse mira), mais rapida. */
  private rebater(bala: Ret): void {
    if (this.escama.nivel('espada') < 2 || bala.getData('rebatida')) return;
    const corpo = bala.body as Phaser.Physics.Arcade.Body;
    this.physics.velocityFromRotation(this.anguloCorte, VEL_BALA * 1.4, corpo.velocity);
    bala.setData('rebatida', true);
    bala.setFillStyle(0x00f0ff);
    bala.setRotation(this.anguloCorte);
    this.cameras.main.shake(60, 0.004);
  }

  /** Angulo de Marco ate o mouse, em coordenadas do mundo (a camera se move). */
  private anguloMira(): number {
    const p = this.input.activePointer.positionToCamera(this.cameras.main) as Phaser.Math.Vector2;
    return Phaser.Math.Angle.Between(this.marco.x, this.marco.y, p.x, p.y);
  }

  private desenharMira(): void {
    const p = this.input.activePointer.positionToCamera(this.cameras.main) as Phaser.Math.Vector2;
    const cor = this.arma === 'canhao' ? 0xffd166 : 0xffffff;
    this.mira.clear();
    this.mira.lineStyle(2, cor, 0.9);
    this.mira.strokeCircle(p.x, p.y, 7);
    this.mira.lineBetween(p.x - 12, p.y, p.x - 4, p.y);
    this.mira.lineBetween(p.x + 4, p.y, p.x + 12, p.y);
    this.mira.lineBetween(p.x, p.y - 12, p.x, p.y - 4);
    this.mira.lineBetween(p.x, p.y + 4, p.x, p.y + 12);
  }

  private acertar(inimigo: Inimigo, direcao: number): void {
    if (!inimigo.vivo) return;
    inimigo.morrer(direcao);
    this.cameras.main.shake(80, 0.006);
  }

  // ------------------------------------------------------------------ fluxo da fase

  private tentarDeNovo(): void {
    this.definirOvertime(false);
    this.scene.restart();
  }

  private concluir(): void {
    this.concluida = true;
    this.definirOvertime(false);
    this.corpo.setVelocity(0, 0);

    const resultado: ResultadoFase = {
      fase: FASE,
      nomeFase: NOME_FASE,
      tempoMs: Math.round(performance.now() - this.registry.get(REG_INICIO)),
      mortes: this.registry.get(REG_MORTES),
    };
    this.registry.remove(REG_INICIO);
    this.registry.remove(REG_MORTES);

    // Libera o teclado para o Angular (campo de nome do ranking)
    this.input.keyboard!.disableGlobalCapture();
    this.input.keyboard!.resetKeys();
    this.game.events.emit(EVENTO_FASE_COMPLETA, resultado);
  }

  // ------------------------------------------------------------------ util

  private inimigosVivos(): number {
    return (this.inimigos.getChildren() as Inimigo[]).filter((i) => i.vivo).length;
  }

  private comoInimigo(a: unknown, b: unknown): Inimigo {
    return (a instanceof Inimigo ? a : b) as Inimigo;
  }

  private comoBala(a: unknown, b: unknown): Ret {
    return ((a as Ret).getData?.('bala') ? a : b) as Ret;
  }

  private definirOvertime(ativo: boolean): void {
    this.physics.world.timeScale = ativo ? FATOR_OVERTIME : 1;
    this.time.timeScale = ativo ? 1 / FATOR_OVERTIME : 1;
    this.filtroOvertime?.setFillStyle(0x6a00ff, ativo ? 0.18 : 0);
  }

  private desenharHud(overtime: boolean, restantes: number): void {
    const g = this.barraVida;
    g.clear();
    g.fillStyle(0x2a1b3d).fillRect(16, 14, 200, 12);
    g.fillStyle(overtime ? 0xb388ff : 0x3dff9a).fillRect(16, 14, 200 * (this.vida / VIDA_MAX), 12);

    const tempo = (performance.now() - (this.registry.get(REG_INICIO) ?? performance.now())) / 1000;
    const hab = this.escama.habilidades;
    this.hud.setText(
      `${tempo.toFixed(2)}s · Mortes: ${this.registry.get(REG_MORTES) ?? 0}\n` +
      (restantes > 0 ? `Inimigos: ${restantes}` : 'Lixão limpo! Vá até a saída →') +
      `\n${this.arma === 'espada' ? '▶ ESPADA' : '  Espada'} nv${hab.espada.nivel}` +
      (hab.canhao.desbloqueada ? `   ${this.arma === 'canhao' ? '▶ CANHÃO' : '  Canhão'} nv${hab.canhao.nivel}   (Q troca)` : '') +
      (hab.overtime.desbloqueada ? `\nOvertime nv${hab.overtime.nivel} (Shift)` : ''),
    );
  }
}
