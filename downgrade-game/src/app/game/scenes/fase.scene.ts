import Phaser from 'phaser';
import { Escama } from '../escama/escama';
import { EVENTO_FASE_COMPLETA, ResultadoFase } from '../eventos';
import { FASES, InfoFase, TILESETS, infoFase } from '../fases/fases';
import { Inimigo, Mundo, Ponto } from '../inimigos/inimigo';
import { CORPO_HUMANO, QUADRO, carregarSprites, criarAnimacoes } from '../sprites';
import { Catador } from '../inimigos/catador';
import { Pistoleiro } from '../inimigos/pistoleiro';

const TELA_W = 960;
const TELA_H = 540;
const VELOCIDADE = 280;
const PULO = 560;
const FATOR_OVERTIME = 3;
const VIDA_MAX = 100;
const VEL_BALA = 520;

// Chaves no registry do jogo: sobrevivem ao restart da cena (tempo e mortes da tentativa)
export const REG_INICIO = 'fase.inicio';
export const REG_MORTES = 'fase.mortes';

/**
 * Em desenvolvimento: Espada nv 2 (rebate balas) e Canhao/Overtime liberados para teste.
 * Na campanha, a fase 1 comeca so com Espada nv 0.
 */
const DEV_LIBERAR_TUDO = true;

type Teclas = Record<'W' | 'A' | 'D' | 'J' | 'Q' | 'R' | 'SPACE' | 'SHIFT', Phaser.Input.Keyboard.Key>;
type Ret = Phaser.GameObjects.Rectangle;
type Sprite = Phaser.GameObjects.Sprite;
type Arma = 'espada' | 'canhao';

/** Metade da altura do sprite humano (32x48): os pes ficam na base do quadro. */
const MEIA_ALTURA = 24;

export interface DadosFase {
  fase?: number;
}

/**
 * Cena generica de fase: carrega o mapa do Tiled da fase pedida.
 * Camadas do mapa:
 *  - `solidos` (tiles): tudo que colide
 *  - `spawns` (objetos): marco, catador, pistoleiro, saida
 */
export class FaseScene extends Phaser.Scene implements Mundo {
  marco!: Sprite;
  private info!: InfoFase;
  private escama!: Escama;
  private corpo!: Phaser.Physics.Arcade.Body;
  private corte!: Ret; // hitbox (invisivel)
  private corteCorpo!: Phaser.Physics.Arcade.Body;
  private efeitoCorte!: Sprite; // arco do corte, rotacionado para o mouse
  private mira!: Phaser.GameObjects.Graphics;
  private fundos: { img: Phaser.GameObjects.TileSprite; fator: number }[] = [];
  private chuva?: Phaser.GameObjects.Particles.ParticleEmitter;
  private solidos!: Phaser.Tilemaps.TilemapLayer;
  private inimigos!: Phaser.Physics.Arcade.Group;
  private balas!: Phaser.Physics.Arcade.Group;
  private tirosMarco!: Phaser.Physics.Arcade.Group;
  private saida!: Sprite;
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
    super('fase');
  }

  // ------------------------------------------------------------------ carregamento

  init(dados: DadosFase): void {
    this.info = infoFase(dados?.fase ?? FASES[0].numero);
  }

  preload(): void {
    for (const [nome, url] of Object.entries(TILESETS)) {
      if (!this.textures.exists(`tileset-${nome}`)) this.load.image(`tileset-${nome}`, url);
    }
    if (!this.cache.tilemap.exists(this.chaveMapa())) this.load.tilemapTiledJSON(this.chaveMapa(), this.info.mapa!);
    for (const f of this.info.fundos ?? []) {
      if (!this.textures.exists(f.url)) this.load.image(f.url, f.url);
    }
    carregarSprites(this);
  }

  private chaveMapa(): string {
    return `mapa-fase-${this.info.numero}`;
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

    criarAnimacoes(this);
    this.criarFundos();
    const mapa = this.criarMapa();
    this.criarArmas();
    this.criarChuva();
    this.criarHud();

    this.physics.world.setBounds(0, 0, mapa.widthInPixels, mapa.heightInPixels);
    this.cameras.main.setBounds(0, 0, mapa.widthInPixels, mapa.heightInPixels);
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

  /** Monta a fase a partir do mapa do Tiled. */
  private criarMapa(): Phaser.Tilemaps.Tilemap {
    const mapa = this.make.tilemap({ key: this.chaveMapa() });

    const tilesets = mapa.tilesets.map((ts) => {
      if (!TILESETS[ts.name]) throw new Error(`Tileset "${ts.name}" não está registrado em fases.ts (TILESETS).`);
      return mapa.addTilesetImage(ts.name, `tileset-${ts.name}`)!;
    });

    this.solidos = mapa.createLayer('solidos', tilesets)!;
    this.solidos.setCollisionByExclusion([-1]);
    if (mapa.getLayer('decoracao')) mapa.createLayer('decoracao', tilesets); // sem colisao

    const fundo = (mapa as unknown as { backgroundColor?: string }).backgroundColor;
    if (fundo) this.cameras.main.setBackgroundColor(fundo);

    this.inimigos = this.physics.add.group({ collideWorldBounds: true });

    for (const o of mapa.getObjectLayer('spawns')?.objects ?? []) {
      const tipo = String(o.type || (o as { class?: string }).class || '').toLowerCase();
      const w = o.width ?? 0;
      const h = o.height ?? 0;
      const cx = (o.x ?? 0) + w / 2;
      const base = (o.y ?? 0) + h; // os pes ficam na base do objeto
      const props: Record<string, unknown> = Object.fromEntries(
        ((o.properties ?? []) as { name: string; value: unknown }[]).map((p) => [p.name, p.value]),
      );

      switch (tipo) {
        case 'marco':
          this.criarMarco(cx, base - MEIA_ALTURA);
          break;
        case 'catador':
          this.adicionarInimigo(new Catador(this, cx, base - MEIA_ALTURA, Number(props['patrulha'] ?? 80)));
          break;
        case 'pistoleiro':
          this.adicionarInimigo(new Pistoleiro(this, cx, base - MEIA_ALTURA));
          break;
        case 'saida':
          this.saida = this.add.sprite(cx, base - 40, 'saida', QUADRO.saida.fechada);
          break;
        default:
          console.warn(`[fase ${this.info.numero}] spawn desconhecido: "${tipo}"`);
      }
    }

    if (!this.marco) throw new Error(`Fase ${this.info.numero}: mapa sem spawn "marco".`);
    if (!this.saida) throw new Error(`Fase ${this.info.numero}: mapa sem "saida".`);

    this.physics.add.collider(this.marco, this.solidos);
    this.physics.add.collider(this.inimigos, this.solidos);
    return mapa;
  }

  private criarMarco(x: number, y: number): void {
    this.marco = this.add.sprite(x, y, 'marco', 0).setDepth(2);
    this.physics.add.existing(this.marco);
    this.corpo = this.marco.body as Phaser.Physics.Arcade.Body;
    this.corpo.setSize(CORPO_HUMANO.w, CORPO_HUMANO.h).setOffset(CORPO_HUMANO.offsetX, CORPO_HUMANO.offsetY);
    this.corpo.setCollideWorldBounds(true);
    this.marco.play('marco-parado');
  }

  private adicionarInimigo(i: Inimigo): void {
    this.inimigos.add(i);
    i.ajustarCorpo();
  }

  /** Camadas de fundo com parallax (ficam presas na tela e rolam a textura). */
  private criarFundos(): void {
    this.fundos = (this.info.fundos ?? []).map((f, i) => ({
      img: this.add.tileSprite(0, 0, TELA_W, TELA_H + 4, f.url).setOrigin(0).setScrollFactor(0).setDepth(-10 + i),
      fator: f.fator,
    }));
  }

  /** Chuva acida diagonal (tambem desacelera no Overtime). */
  private criarChuva(): void {
    if (!this.textures.exists('gota')) {
      const g = this.make.graphics({}, false);
      g.fillStyle(0xb8a8e0, 1).fillRect(0, 0, 1, 7);
      g.generateTexture('gota', 1, 7);
      g.destroy();
    }
    this.chuva = this.add.particles(0, 0, 'gota', {
      x: { min: -40, max: TELA_W + 160 },
      y: -12,
      lifespan: 800,
      speedY: { min: 650, max: 850 },
      speedX: { min: -170, max: -130 },
      rotate: 11,
      alpha: { min: 0.12, max: 0.4 },
      quantity: 2,
      frequency: 14,
    }).setScrollFactor(0).setDepth(9);
  }

  private criarArmas(): void {
    // Espada: hitbox quadrada (Arcade nao rotaciona corpos) + lamina visual rotacionada
    const tamHitbox = this.escama.alcanceEspada() * 0.8;
    this.corte = this.add.rectangle(0, 0, tamHitbox, tamHitbox).setVisible(false);
    // arco 48x48 com centro em (10, 24); escala 2 para cobrir a hitbox
    this.efeitoCorte = this.add.sprite(0, 0, 'corte', 0).setOrigin(10 / 48, 0.5).setScale(2).setVisible(false).setDepth(3);
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
      this.acertar(this.comoInimigo(a, b), Math.sign(bala.body!.velocity.x) || 1);
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
    this.rolarFundos();
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

    this.animarMarco(vx);

    for (const i of this.inimigos.getChildren() as Inimigo[]) i.pensar(this);

    const restantes = this.inimigosVivos();
    this.saida.setFrame(restantes === 0 ? QUADRO.saida.aberta : QUADRO.saida.fechada);
    if (restantes === 0 && Phaser.Geom.Rectangle.Overlaps(this.marco.getBounds(), this.saida.getBounds())) {
      return this.concluir();
    }

    this.desenharHud(overtime, restantes);
  }

  // ------------------------------------------------------------------ Mundo (usado pelos inimigos)

  marcoVivo(): boolean {
    return !this.morto && !this.concluida;
  }

  temVisao(de: Ponto, para: Ponto): boolean {
    const linha = new Phaser.Geom.Line(de.x, de.y - 10, para.x, para.y - 10);
    return this.solidos.getTilesWithinShape(linha, { isColliding: true }).length === 0;
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
    this.marco.stop().setFrame(QUADRO.marco.morto).setTint(0x8a7a9a);
    this.efeitoCorte.setVisible(false);
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
    this.efeitoCorte.setVisible(true).play('corte');
    this.marco.play('marco-ataque');
    this.corteCorpo.enable = true;
    this.posicionarCorte();
    this.time.delayedCall(120, () => {
      this.atacando = false;
      this.efeitoCorte.setVisible(false);
      this.corteCorpo.enable = false;
    });
  }

  /** O corte acompanha Marco, mas o angulo fica travado no momento do golpe. */
  private posicionarCorte(): void {
    const dist = this.escama.alcanceEspada() / 2 + 8;
    const cos = Math.cos(this.anguloCorte);
    const sin = Math.sin(this.anguloCorte);
    this.corte.setPosition(this.marco.x + cos * dist, this.marco.y + sin * dist);
    this.corteCorpo.reset(this.corte.x, this.corte.y);
    this.efeitoCorte.setPosition(this.marco.x + cos * 4, this.marco.y + sin * 4).setRotation(this.anguloCorte);
  }

  /** Escolhe a animacao do Marco pelo estado (ataque > ar > correndo > parado). */
  private animarMarco(vx: number): void {
    this.marco.setFlipX(this.direcao < 0);
    if (this.marco.anims.isPlaying && this.marco.anims.currentAnim?.key === 'marco-ataque') return;
    if (!this.corpo.blocked.down) {
      this.marco.stop();
      this.marco.setFrame(this.corpo.velocity.y < 0 ? QUADRO.marco.subindo : QUADRO.marco.caindo);
    } else if (vx !== 0) {
      this.marco.play('marco-correr', true);
    } else {
      this.marco.play('marco-parado', true);
    }
  }

  private rolarFundos(): void {
    const cam = this.cameras.main;
    for (const f of this.fundos) {
      f.img.tilePositionX = cam.scrollX * f.fator;
      f.img.tilePositionY = cam.scrollY * f.fator;
    }
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

  private acertar(inimigo: Inimigo, direcao: number): void {
    if (!inimigo.vivo) return;
    inimigo.morrer(direcao);
    this.cameras.main.shake(80, 0.006);
  }

  /** Angulo de Marco ate o mouse, em coordenadas do mundo (a camera se move). */
  private anguloMira(): number {
    const p = this.input.activePointer.positionToCamera(this.cameras.main) as Phaser.Math.Vector2;
    return Phaser.Math.Angle.Between(this.marco.x, this.marco.y, p.x, p.y);
  }

  // ------------------------------------------------------------------ fluxo da fase

  private tentarDeNovo(): void {
    this.definirOvertime(false);
    this.scene.restart({ fase: this.info.numero } satisfies DadosFase);
  }

  private concluir(): void {
    this.concluida = true;
    this.definirOvertime(false);
    this.corpo.setVelocity(0, 0);
    this.marco.play('marco-parado');

    const resultado: ResultadoFase = {
      fase: this.info.numero,
      nomeFase: `Fase ${this.info.numero} — ${this.info.nome}`,
      tempoMs: Math.round(performance.now() - this.registry.get(REG_INICIO)),
      mortes: this.registry.get(REG_MORTES),
    };
    this.registry.remove(REG_INICIO);
    this.registry.remove(REG_MORTES);

    // Libera o teclado e o cursor para o Angular (campo de nome do ranking)
    this.input.setDefaultCursor('default');
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
    const escala = ativo ? 1 / FATOR_OVERTIME : 1;
    this.physics.world.timeScale = ativo ? FATOR_OVERTIME : 1;
    this.time.timeScale = escala;
    this.anims.globalTimeScale = escala;
    this.tweens.timeScale = escala;
    if (this.chuva) this.chuva.timeScale = escala;
    this.filtroOvertime?.setFillStyle(0x6a00ff, ativo ? 0.18 : 0);
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

  private desenharHud(overtime: boolean, restantes: number): void {
    const g = this.barraVida;
    g.clear();
    g.fillStyle(0x2a1b3d).fillRect(16, 14, 200, 12);
    g.fillStyle(overtime ? 0xb388ff : 0x3dff9a).fillRect(16, 14, 200 * (this.vida / VIDA_MAX), 12);

    const tempo = (performance.now() - (this.registry.get(REG_INICIO) ?? performance.now())) / 1000;
    const hab = this.escama.habilidades;
    this.hud.setText(
      `FASE ${this.info.numero} — ${this.info.nome.toUpperCase()}\n` +
      `${tempo.toFixed(2)}s · Mortes: ${this.registry.get(REG_MORTES) ?? 0}\n` +
      (restantes > 0 ? `Inimigos: ${restantes}` : 'Área limpa! Vá até a saída →') +
      `\n${this.arma === 'espada' ? '▶ ESPADA' : '  Espada'} nv${hab.espada.nivel}` +
      (hab.canhao.desbloqueada ? `   ${this.arma === 'canhao' ? '▶ CANHÃO' : '  Canhão'} nv${hab.canhao.nivel}   (Q troca)` : '') +
      (hab.overtime.desbloqueada ? `\nOvertime nv${hab.overtime.nivel} (Shift)` : ''),
    );
  }
}
