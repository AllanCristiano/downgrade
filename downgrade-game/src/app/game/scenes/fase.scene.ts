import Phaser from 'phaser';
import { Escama } from '../escama/escama';
import { Arma, EfeitosCamera, EstadoFase, ZOOM } from '../estado';
import { EVENTO_FASE_COMPLETA, ResultadoFase } from '../eventos';
import { FASES, InfoFase, TILESETS, infoFase } from '../fases/fases';
import { Inimigo, Mundo, Ponto } from '../inimigos/inimigo';
import { Catador } from '../inimigos/catador';
import { Pistoleiro } from '../inimigos/pistoleiro';
import { CORPO_HUMANO, MEIA_ALTURA_SPRITE, carregarSprites } from '../sprites';

const VELOCIDADE = 270;
const PULO = 560;
const FATOR_OVERTIME = 3;
const VIDA_MAX = 100;
const VEL_BALA = 430;
const ADD = Phaser.BlendModes.ADD;

// Chaves no registry do jogo: sobrevivem ao restart da cena (tempo e mortes da tentativa)
export const REG_INICIO = 'fase.inicio';
export const REG_MORTES = 'fase.mortes';

/**
 * Em desenvolvimento: Espada nv 2 (rebate balas) e Canhao/Overtime liberados para teste.
 * Na campanha, a fase 1 comeca so com Espada nv 0.
 */
const DEV_LIBERAR_TUDO = true;

type Teclas = Record<'W' | 'A' | 'D' | 'J' | 'Q' | 'R' | 'SPACE' | 'SHIFT', Phaser.Input.Keyboard.Key>;
type Sprite = Phaser.GameObjects.Sprite;

export interface DadosFase {
  fase?: number;
}

/** Luz de cada objeto animado do mapa: cor, tamanho, intensidade e se tremula. */
const LUZES: Record<string, { cor: number; escala: number; alfa: number; dy: number; tremula?: boolean }> = {
  neon: { cor: 0xff2a6d, escala: 1.5, alfa: 0.32, dy: -26, tremula: true },
  barril_fogo: { cor: 0xff7a28, escala: 1.3, alfa: 0.5, dy: -30, tremula: true },
  poste: { cor: 0xffd27a, escala: 0.7, alfa: 0.45, dy: -82 },
  tv: { cor: 0x00f0ff, escala: 0.6, alfa: 0.3, dy: -12, tremula: true },
  barril_toxico: { cor: 0x3dff9a, escala: 0.7, alfa: 0.3, dy: -20 },
};

/**
 * Cena generica de fase: carrega o mapa do Tiled da fase pedida.
 * Camadas: `decoracao` (tiles, sem colisao), `solidos` (tiles que colidem),
 * `animados` (objetos com animacao e luz) e `spawns` (marco, inimigos, saida).
 */
export class FaseScene extends Phaser.Scene implements Mundo, EstadoFase {
  marco!: Sprite;
  info?: InfoFase;
  escama?: Escama;
  inicioId = 0;
  vida = VIDA_MAX;
  readonly vidaMax = VIDA_MAX;
  arma: Arma = 'espada';
  overtime = false;
  morto = false;
  motivoMorte = '';
  concluida = false;

  private corpo!: Phaser.Physics.Arcade.Body;
  private corte!: Phaser.GameObjects.Rectangle; // hitbox invisivel do golpe
  private corteCorpo!: Phaser.Physics.Arcade.Body;
  private efeitoCorte!: Sprite;
  private mira!: Phaser.GameObjects.Graphics;
  private solidos!: Phaser.Tilemaps.TilemapLayer;
  private inimigos!: Phaser.Physics.Arcade.Group;
  private balas!: Phaser.Physics.Arcade.Group;
  private tirosMarco!: Phaser.Physics.Arcade.Group;
  private saida!: Sprite;
  private luzSaida!: Phaser.GameObjects.Image;
  private luzEscama!: Phaser.GameObjects.Image;
  private efeitos?: EfeitosCamera;
  private teclas!: Teclas;

  private direcao = 1;
  private anguloCorte = 0;
  private atacando = false;
  private ultimoTiro = 0;
  private noChao = true;
  private velQueda = 0;
  private ultimaPoeira = 0;
  private hitStopId = 0;

  constructor() {
    super('fase');
  }

  // ------------------------------------------------------------------ estado para HUD/fundo

  get tempoMs(): number {
    const inicio = this.registry.get(REG_INICIO);
    return inicio === undefined ? 0 : performance.now() - inicio;
  }

  get mortes(): number {
    return this.registry.get(REG_MORTES) ?? 0;
  }

  get restantes(): number {
    return this.inimigos ? (this.inimigos.getChildren() as Inimigo[]).filter((i) => i.vivo).length : 0;
  }

  // ------------------------------------------------------------------ carregamento

  init(dados: DadosFase): void {
    this.info = infoFase(dados?.fase ?? FASES[0].numero);
  }

  preload(): void {
    const info = this.info!;
    for (const [nome, url] of Object.entries(TILESETS)) {
      if (!this.textures.exists(`tileset-${nome}`)) this.load.image(`tileset-${nome}`, url);
    }
    if (!this.cache.tilemap.exists(this.chaveMapa())) this.load.tilemapTiledJSON(this.chaveMapa(), info.mapa!);
    for (const f of info.fundos ?? []) {
      if (!this.textures.exists(f.url)) this.load.image(f.url, f.url);
    }
    carregarSprites(this);
  }

  private chaveMapa(): string {
    return `mapa-fase-${this.info!.numero}`;
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
    this.overtime = false;
    this.motivoMorte = '';
    this.noChao = true;
    this.inicioId++;

    if (this.registry.get(REG_INICIO) === undefined) {
      this.registry.set(REG_INICIO, performance.now());
      this.registry.set(REG_MORTES, 0);
    }

    const cam = this.cameras.main;
    cam.setZoom(ZOOM).setRoundPixels(true);
    this.efeitos = new EfeitosCamera(this, cam);

    const mapa = this.criarMapa();
    this.criarArmas();

    this.physics.world.setBounds(0, 0, mapa.widthInPixels, mapa.heightInPixels);
    cam.setBounds(0, 0, mapa.widthInPixels, mapa.heightInPixels);
    cam.startFollow(this.marco, true, 0.14, 0.14, 0, 18);
    cam.setDeadzone(40, 50);

    this.iniciarCenasAuxiliares();

    this.input.keyboard!.enableGlobalCapture();
    this.teclas = this.input.keyboard!.addKeys('W,A,D,J,Q,R,SPACE,SHIFT') as Teclas;
    this.input.setDefaultCursor('none');
    this.input.on('pointerdown', (p: Phaser.Input.Pointer) => {
      if (!p.leftButtonDown()) return;
      if (this.morto) this.tentarDeNovo();
      else this.atacar();
    });
  }

  private iniciarCenasAuxiliares(): void {
    if (!this.scene.isActive('fundo')) this.scene.launch('fundo');
    if (!this.scene.isActive('hud')) this.scene.launch('hud');
    this.scene.sendToBack('fundo');
    this.scene.bringToTop('hud');
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

    if (mapa.getLayer('decoracao')) mapa.createLayer('decoracao', tilesets)!.setDepth(0);
    this.solidos = mapa.createLayer('solidos', tilesets)!.setDepth(0);
    this.solidos.setCollisionByExclusion([-1]);

    for (const o of mapa.getObjectLayer('animados')?.objects ?? []) {
      const { tipo, cx, base } = lerObjeto(o);
      this.criarAnimado(tipo, cx, base);
    }

    this.inimigos = this.physics.add.group({ collideWorldBounds: true });
    for (const o of mapa.getObjectLayer('spawns')?.objects ?? []) {
      const { tipo, cx, base, props } = lerObjeto(o);
      const y = base - MEIA_ALTURA_SPRITE;
      switch (tipo) {
        case 'marco':
          this.criarMarco(cx, y);
          break;
        case 'catador':
          this.adicionarInimigo(new Catador(this, cx, y, Number(props['patrulha'] ?? 80)));
          break;
        case 'pistoleiro':
          this.adicionarInimigo(new Pistoleiro(this, cx, y));
          break;
        case 'saida':
          this.saida = this.add.sprite(cx, base - 48, 'saida').play('saida-fechada').setDepth(1);
          this.luzSaida = this.luz(cx, base - 92, 0xff2a6d, 0.6, 0.4);
          break;
        default:
          console.warn(`[fase ${this.info!.numero}] spawn desconhecido: "${tipo}"`);
      }
    }
    if (!this.marco) throw new Error(`Fase ${this.info!.numero}: mapa sem spawn "marco".`);
    if (!this.saida) throw new Error(`Fase ${this.info!.numero}: mapa sem "saida".`);

    this.physics.add.collider(this.marco, this.solidos);
    this.physics.add.collider(this.inimigos, this.solidos);
    return mapa;
  }

  private criarAnimado(tipo: string, cx: number, base: number): void {
    const s = this.add.sprite(cx, base, tipo).setOrigin(0.5, 1).setDepth(1);
    s.play({ key: `${tipo}-loop`, startFrame: Phaser.Math.Between(0, 3) });
    const l = LUZES[tipo];
    if (!l) return;
    const luz = this.luz(cx, base + l.dy, l.cor, l.escala, l.alfa);
    if (tipo === 'poste') {
      this.add.image(cx + 7, base + l.dy + 2, 'cone').setOrigin(0.5, 0).setBlendMode(ADD)
        .setTint(l.cor).setAlpha(0.22).setScale(0.55, 0.55).setDepth(6);
    }
    if (l.tremula) {
      this.tweens.add({
        targets: luz, alpha: { from: l.alfa * 0.6, to: l.alfa }, scale: { from: l.escala * 0.94, to: l.escala },
        duration: Phaser.Math.Between(90, 200), yoyo: true, repeat: -1, ease: 'Sine.easeInOut',
      });
    }
  }

  /** Luz aditiva (glow) — e o que faz o neon "acender". */
  private luz(x: number, y: number, cor: number, escala: number, alfa: number): Phaser.GameObjects.Image {
    return this.add.image(x, y, 'luz').setBlendMode(ADD).setTint(cor).setScale(escala).setAlpha(alfa).setDepth(6);
  }

  private criarMarco(x: number, y: number): void {
    this.marco = this.add.sprite(x, y, 'marco').setDepth(3);
    this.physics.add.existing(this.marco);
    this.corpo = this.marco.body as Phaser.Physics.Arcade.Body;
    this.corpo.setSize(CORPO_HUMANO.w, CORPO_HUMANO.h).setOffset(CORPO_HUMANO.offsetX, CORPO_HUMANO.offsetY);
    this.corpo.setCollideWorldBounds(true);
    this.marco.play('marco-parado');
    this.luzEscama = this.luz(x, y, 0x00f0ff, 0.22, 0.5);
  }

  private adicionarInimigo(i: Inimigo): void {
    this.inimigos.add(i);
    i.ajustarCorpo();
  }

  private criarArmas(): void {
    const tamHitbox = this.escama!.alcanceEspada() * 0.8;
    this.corte = this.add.rectangle(0, 0, tamHitbox, tamHitbox).setVisible(false);
    this.physics.add.existing(this.corte);
    this.corteCorpo = this.corte.body as Phaser.Physics.Arcade.Body;
    this.corteCorpo.setAllowGravity(false);
    this.corteCorpo.enable = false;
    // arco 96x96 com o centro do arco em (24, 48)
    this.efeitoCorte = this.add.sprite(0, 0, 'corte').setOrigin(24 / 96, 0.5).setVisible(false).setDepth(4).setBlendMode(ADD);
    this.mira = this.add.graphics().setDepth(20);

    this.balas = this.physics.add.group({ allowGravity: false });
    this.tirosMarco = this.physics.add.group({ allowGravity: false });

    const vivo = (a: unknown, b: unknown) => this.comoInimigo(a, b).vivo;

    // Espada mata inimigos
    this.physics.add.overlap(this.corte, this.inimigos,
      (a, b) => this.acertar(this.comoInimigo(a, b), Math.sign(Math.cos(this.anguloCorte)) || 1), vivo);
    // Espada nv 2+ rebate balas
    this.physics.add.overlap(this.corte, this.balas, (a, b) => this.rebater(this.comoBala(a, b)));
    // Bala inimiga mata Marco
    this.physics.add.overlap(this.marco, this.balas, (a, b) => {
      this.comoBala(a, b).destroy();
      this.matarMarco('LEVOU UM TIRO.');
    }, (a, b) => !this.comoBala(a, b).getData('rebatida') && this.marcoVivo());
    // Bala rebatida mata inimigo
    this.physics.add.overlap(this.balas, this.inimigos, (a, b) => {
      const bala = this.comoBala(a, b);
      this.acertar(this.comoInimigo(a, b), Math.sign(bala.body!.velocity.x) || 1);
      bala.destroy();
    }, (a, b) => this.comoBala(a, b).getData('rebatida') && vivo(a, b));
    // Canhao de Marco
    this.physics.add.overlap(this.tirosMarco, this.inimigos, (a, b) => {
      const tiro = this.comoBala(a, b);
      this.acertar(this.comoInimigo(a, b), Math.sign(tiro.body!.velocity.x) || 1);
      this.fx('impacto_canhao', 'estouro', tiro.x, tiro.y);
    }, vivo);
    // Tudo que voa morre na parede
    this.physics.add.collider(this.balas, this.solidos, (a, b) => {
      const bala = this.comoBala(a, b);
      this.fx('faisca', 'estouro', bala.x, bala.y, { escala: 0.5 });
      bala.destroy();
    });
    this.physics.add.collider(this.tirosMarco, this.solidos, (a, b) => {
      const tiro = this.comoBala(a, b);
      this.fx('impacto_canhao', 'estouro', tiro.x, tiro.y);
      tiro.destroy();
    });
  }

  // ------------------------------------------------------------------ loop

  override update(_time: number, delta: number): void {
    const t = this.teclas;
    if (this.concluida) return;

    this.desenharMira();
    this.acompanharLuzEscama();

    if (this.morto) {
      if (Phaser.Input.Keyboard.JustDown(t.R) || Phaser.Input.Keyboard.JustDown(t.J)) this.tentarDeNovo();
      return;
    }
    if (Phaser.Input.Keyboard.JustDown(t.R)) return this.tentarDeNovo();

    // Overtime: camera lenta que drena vida (delta e tempo real)
    const overtime = this.escama!.tem('overtime') && t.SHIFT.isDown;
    this.definirOvertime(overtime);
    if (overtime) {
      this.vida = Math.max(0, this.vida - this.escama!.drenoOvertime() * (delta / 1000));
      if (this.vida <= 0) return this.matarMarco('A ESCAMA CONSUMIU MARCO.\nOVERTIME DEMAIS.');
    }

    // Movimento
    let vx = 0;
    if (t.A.isDown) vx -= VELOCIDADE;
    if (t.D.isDown) vx += VELOCIDADE;
    if (vx !== 0 && !this.atacando) this.direcao = Math.sign(vx);
    this.corpo.setVelocityX(vx);
    if ((Phaser.Input.Keyboard.JustDown(t.W) || Phaser.Input.Keyboard.JustDown(t.SPACE)) && this.corpo.blocked.down) {
      this.corpo.setVelocityY(-PULO);
      this.marco.play('marco-pulo');
      this.fx('poeira', 'nuvem', this.marco.x, this.marco.y + 26, { escala: 0.8 });
    }

    if (Phaser.Input.Keyboard.JustDown(t.Q)) this.trocarArma();
    if (Phaser.Input.Keyboard.JustDown(t.J)) this.atacar();
    if (this.atacando) this.posicionarCorte();

    this.animarMarco(vx);

    for (const i of this.inimigos.getChildren() as Inimigo[]) i.pensar(this);

    if (this.restantes === 0 && this.saida.anims.currentAnim?.key === 'saida-fechada') {
      this.saida.play('saida-abrindo').chain('saida-aberta');
      this.luzSaida.setTint(0x3dff9a);
    }
    if (this.restantes === 0 && Phaser.Geom.Rectangle.Overlaps(this.corpo.getBounds(new Phaser.Geom.Rectangle()) as Phaser.Geom.Rectangle, this.saida.getBounds())) {
      this.concluir();
    }
  }

  // ------------------------------------------------------------------ Mundo (usado pelos inimigos)

  marcoVivo(): boolean {
    return !this.morto && !this.concluida;
  }

  temVisao(de: Ponto, para: Ponto): boolean {
    const linha = new Phaser.Geom.Line(de.x, de.y - 8, para.x, para.y - 8);
    return this.solidos.getTilesWithinShape(linha, { isColliding: true }).length === 0;
  }

  dispararBala(x: number, y: number, angulo: number): void {
    const bala = this.add.sprite(x, y, 'bala').setRotation(angulo).setDepth(5).setBlendMode(ADD);
    bala.setData('bala', true);
    this.balas.add(bala);
    const corpo = bala.body as Phaser.Physics.Arcade.Body;
    corpo.setSize(6, 6).setOffset(10, 0);
    this.physics.velocityFromRotation(angulo, VEL_BALA, corpo.velocity);
    this.fx('clarao', 'tiro', x, y, { rotacao: angulo, origemX: 6 / 24 });
    this.time.delayedCall(2500, () => bala.destroy());
  }

  matarMarco(motivo: string): void {
    if (this.morto || this.concluida) return;
    this.morto = true;
    this.motivoMorte = motivo;
    this.registry.inc(REG_MORTES, 1);
    this.definirOvertime(false);
    this.corpo.setVelocity(0, 0);
    this.corpo.setAllowGravity(true);
    this.efeitoCorte.setVisible(false);
    this.corteCorpo.enable = false;
    this.marco.play('marco-morte');
    this.fx('sangue', 'respingo', this.marco.x, this.marco.y - 6, { flip: this.direcao > 0 });
    this.tweens.add({ targets: this.luzEscama, alpha: 0, duration: 900 });
    this.cameras.main.shake(180, 0.008);
    this.cameras.main.flash(140, 255, 42, 109);
  }

  // ------------------------------------------------------------------ acoes de Marco

  /** Q: alterna Espada <-> Canhao (se o Canhao ja foi absorvido). */
  private trocarArma(): void {
    if (!this.escama!.tem('canhao')) return;
    this.arma = this.arma === 'espada' ? 'canhao' : 'espada';
  }

  /** Clique / J: usa a arma atual na direcao do mouse. */
  private atacar(): void {
    if (this.morto || this.concluida) return;
    if (this.arma === 'canhao') return this.atirar();
    if (this.atacando) return;

    const ang = this.anguloMira();
    this.anguloCorte = ang;
    const graus = Phaser.Math.RadToDeg(ang);
    if (Math.abs(Math.cos(ang)) > 0.2) this.direcao = Math.cos(ang) >= 0 ? 1 : -1;
    // ataque para cima, para baixo ou para frente conforme o angulo do mouse
    const anim = graus < -55 && graus > -125 ? 'marco-ataque_cima' : graus > 55 && graus < 125 ? 'marco-ataque_baixo' : 'marco-ataque_frente';
    this.marco.setFlipX(this.direcao < 0).play(anim);

    this.atacando = true;
    this.efeitoCorte.setVisible(true).setFlipY(Math.cos(ang) < 0).play('corte-golpe');
    this.corteCorpo.enable = true;
    this.posicionarCorte();
    this.time.delayedCall(130, () => {
      this.atacando = false;
      this.corteCorpo.enable = false;
    });
    this.efeitoCorte.once(Phaser.Animations.Events.ANIMATION_COMPLETE, () => this.efeitoCorte.setVisible(false));
  }

  /** O corte acompanha Marco, mas o angulo fica travado no momento do golpe. */
  private posicionarCorte(): void {
    const dist = this.escama!.alcanceEspada() / 2 + 8;
    const cos = Math.cos(this.anguloCorte);
    const sin = Math.sin(this.anguloCorte);
    const cy = this.marco.y - 4;
    this.corte.setPosition(this.marco.x + cos * dist, cy + sin * dist);
    this.corteCorpo.reset(this.corte.x, this.corte.y);
    this.efeitoCorte.setPosition(this.marco.x + cos * 2, cy + sin * 2).setRotation(this.anguloCorte);
  }

  private atirar(): void {
    if (!this.escama!.tem('canhao')) return;
    if (this.time.now - this.ultimoTiro < this.escama!.recargaCanhao()) return;
    this.ultimoTiro = this.time.now;

    const ang = this.anguloMira();
    if (Math.abs(Math.cos(ang)) > 0.2) this.direcao = Math.cos(ang) >= 0 ? 1 : -1;
    this.marco.setFlipX(this.direcao < 0).play('marco-canhao');
    const ox = this.marco.x + this.direcao * 20;
    const oy = this.marco.y - 6;
    const tiro = this.add.sprite(ox, oy, 'tiro_canhao').play('tiro_canhao-voo').setRotation(ang).setDepth(5).setBlendMode(ADD);
    tiro.setData('bala', true);
    this.tirosMarco.add(tiro);
    const corpo = tiro.body as Phaser.Physics.Arcade.Body;
    corpo.setSize(8, 8).setOffset(14, 2);
    this.physics.velocityFromRotation(ang, 900, corpo.velocity);
    this.fx('clarao', 'tiro', ox, oy, { rotacao: ang, origemX: 6 / 24 });
    this.cameras.main.shake(70, 0.003);
    this.time.delayedCall(1200, () => tiro.destroy());
  }

  /** Espada nv 2+: a bala volta na direcao do corte (para onde o mouse mira), mais rapida. */
  private rebater(bala: Sprite): void {
    if (this.escama!.nivel('espada') < 2 || bala.getData('rebatida')) return;
    const corpo = bala.body as Phaser.Physics.Arcade.Body;
    this.physics.velocityFromRotation(this.anguloCorte, VEL_BALA * 1.5, corpo.velocity);
    bala.setData('rebatida', true).setTexture('bala_rebatida').setRotation(this.anguloCorte);
    this.fx('faisca', 'estouro', bala.x, bala.y);
    this.cameras.main.shake(70, 0.004);
    this.hitStop(45);
  }

  private acertar(inimigo: Inimigo, direcao: number): void {
    if (!inimigo.vivo) return;
    inimigo.morrer(direcao);
    this.fx('sangue', 'respingo', inimigo.x, inimigo.y - 8, { flip: direcao < 0 });
    this.absorverFragmentos(inimigo.x, inimigo.y - 10);
    this.cameras.main.shake(90, 0.006);
    this.hitStop(60);
  }

  /** Fragmentos das Escamas piratas voando para a Escama de Marco. */
  private absorverFragmentos(x: number, y: number): void {
    for (let i = 0; i < 6; i++) {
      const f = this.add.image(x, y, 'fragmento').setBlendMode(ADD).setDepth(7);
      const ang = Math.random() * Math.PI * 2;
      this.tweens.chain({
        targets: f,
        tweens: [
          { x: x + Math.cos(ang) * 22, y: y + Math.sin(ang) * 22, duration: 180, ease: 'Cubic.easeOut' },
          {
            x: { getEnd: () => this.marco.x }, y: { getEnd: () => this.marco.y - 14 },
            duration: 260, delay: i * 25, ease: 'Cubic.easeIn',
            onComplete: () => {
              f.destroy();
              this.luzEscama.setScale(0.4);
            },
          },
        ],
      });
    }
  }

  // ------------------------------------------------------------------ animacao e efeitos

  /** Escolhe a animacao do Marco pelo estado (golpe > ar > aterrissagem > correndo > parado). */
  private animarMarco(vx: number): void {
    this.marco.setFlipX(this.direcao < 0);
    const atual = this.marco.anims.currentAnim?.key ?? '';
    const tocando = this.marco.anims.isPlaying;
    const noChao = this.corpo.blocked.down;

    if (!this.noChao && noChao) {
      // acabou de aterrissar
      if (this.velQueda > 250) {
        this.fx('poeira', 'nuvem', this.marco.x, this.marco.y + 26);
        if (vx === 0) this.marco.play('marco-aterrissar');
      }
    }
    this.noChao = noChao;
    this.velQueda = this.corpo.velocity.y;

    const travada = ['marco-ataque_frente', 'marco-ataque_cima', 'marco-ataque_baixo', 'marco-canhao'];
    if (tocando && travada.includes(atual)) return;

    if (!noChao) {
      if (tocando && atual === 'marco-pulo') return;
      const vy = this.corpo.velocity.y;
      this.marco.play(vy < -60 ? 'marco-subindo' : vy > 60 ? 'marco-caindo' : 'marco-apice', true);
      return;
    }
    if (vx !== 0) {
      this.marco.play('marco-correr', true);
      if (this.time.now - this.ultimaPoeira > 260) {
        this.ultimaPoeira = this.time.now;
        this.fx('poeira', 'nuvem', this.marco.x - this.direcao * 8, this.marco.y + 28, { escala: 0.5, alfa: 0.6 });
      }
      return;
    }
    if (tocando && atual === 'marco-aterrissar') return;
    this.marco.play('marco-parado', true);
  }

  private acompanharLuzEscama(): void {
    // a Escama fica na nuca: atras da cabeca, do lado oposto ao que Marco olha
    this.luzEscama.setPosition(this.marco.x - this.direcao * 4, this.marco.y - 14);
    if (this.luzEscama.scale > 0.22) this.luzEscama.setScale(Math.max(0.22, this.luzEscama.scale - 0.01));
  }

  /** Toca um efeito de uma vez so e remove no fim. */
  private fx(folha: string, anim: string, x: number, y: number,
    o: { rotacao?: number; flip?: boolean; escala?: number; alfa?: number; origemX?: number } = {}): void {
    const s = this.add.sprite(x, y, folha).setDepth(8).setBlendMode(folha === 'sangue' || folha === 'poeira' ? Phaser.BlendModes.NORMAL : ADD);
    s.setRotation(o.rotacao ?? 0).setFlipX(!!o.flip).setScale(o.escala ?? 1).setAlpha(o.alfa ?? 1);
    if (o.origemX !== undefined) s.setOrigin(o.origemX, 0.5);
    if (folha === 'sangue') s.setOrigin(o.flip ? 1 - 12 / 48 : 12 / 48, 0.5);
    s.play(`${folha}-${anim}`).once(Phaser.Animations.Events.ANIMATION_COMPLETE, () => s.destroy());
  }

  /** Congela o jogo por alguns ms no impacto (sensacao de peso no golpe). */
  private hitStop(ms: number): void {
    const id = ++this.hitStopId;
    const inicio = this.inicioId;
    this.physics.world.pause();
    this.anims.pauseAll();
    this.time.paused = true;
    window.setTimeout(() => {
      if (id !== this.hitStopId || inicio !== this.inicioId || !this.sys.isActive()) return;
      this.physics.world.resume();
      this.anims.resumeAll();
      this.time.paused = false;
    }, ms);
  }

  // ------------------------------------------------------------------ fluxo da fase

  private tentarDeNovo(): void {
    this.liberarHitStop();
    this.definirOvertime(false);
    this.scene.restart({ fase: this.info!.numero } satisfies DadosFase);
  }

  private liberarHitStop(): void {
    this.hitStopId++;
    this.physics.world.resume();
    this.anims.resumeAll();
    this.time.paused = false;
  }

  private concluir(): void {
    this.concluida = true;
    this.liberarHitStop();
    this.definirOvertime(false);
    this.corpo.setVelocity(0, 0);
    this.marco.play('marco-parado');

    const resultado: ResultadoFase = {
      fase: this.info!.numero,
      nomeFase: `Fase ${this.info!.numero} — ${this.info!.nome}`,
      tempoMs: Math.round(this.tempoMs),
      mortes: this.mortes,
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

  private anguloMira(): number {
    const p = this.input.activePointer.positionToCamera(this.cameras.main) as Phaser.Math.Vector2;
    return Phaser.Math.Angle.Between(this.marco.x, this.marco.y - 4, p.x, p.y);
  }

  private comoInimigo(a: unknown, b: unknown): Inimigo {
    return (a instanceof Inimigo ? a : b) as Inimigo;
  }

  private comoBala(a: unknown, b: unknown): Sprite {
    return ((a as Sprite).getData?.('bala') ? a : b) as Sprite;
  }

  private definirOvertime(ativo: boolean): void {
    this.overtime = ativo;
    const escala = ativo ? 1 / FATOR_OVERTIME : 1;
    this.physics.world.timeScale = ativo ? FATOR_OVERTIME : 1;
    this.time.timeScale = escala;
    this.anims.globalTimeScale = escala;
    this.tweens.timeScale = escala;
    this.efeitos?.overtime(ativo);
  }

  private desenharMira(): void {
    const p = this.input.activePointer.positionToCamera(this.cameras.main) as Phaser.Math.Vector2;
    const cor = this.arma === 'canhao' ? 0xffd166 : 0x00f0ff;
    const m = this.mira;
    m.clear();
    m.lineStyle(1, 0x07010f, 0.8).strokeCircle(p.x, p.y, 5.5);
    m.lineStyle(1, cor, 1).strokeCircle(p.x, p.y, 4.5);
    m.fillStyle(0xffffff, 1).fillRect(p.x - 0.5, p.y - 0.5, 1, 1);
    for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      m.lineStyle(1, cor, 1).lineBetween(p.x + dx * 7, p.y + dy * 7, p.x + dx * 10, p.y + dy * 10);
    }
  }
}

/** Le um objeto do Tiled: classe, centro x e base (os pes ficam na base do retangulo). */
function lerObjeto(o: Phaser.Types.Tilemaps.TiledObject) {
  const tipo = String(o.type || (o as { class?: string }).class || '').toLowerCase();
  const w = o.width ?? 0;
  const h = o.height ?? 0;
  const props: Record<string, unknown> = Object.fromEntries(
    ((o.properties ?? []) as { name: string; value: unknown }[]).map((p) => [p.name, p.value]),
  );
  return { tipo, cx: (o.x ?? 0) + w / 2, base: (o.y ?? 0) + h, props };
}
