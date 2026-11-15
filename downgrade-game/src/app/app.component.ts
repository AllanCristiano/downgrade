import { Component, OnInit, inject, signal, viewChild } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { GameComponent } from './game/game.component';
import { ResultadoFase } from './game/eventos';
import { FASES } from './game/fases/fases';
import { RankingService, Score } from './ranking.service';

type Status = 'verificando' | 'online' | 'offline';

const CHAVE_NOME = 'downgrade.nome';

function lerNome(): string {
  try {
    return localStorage.getItem(CHAVE_NOME) || 'MARCO';
  } catch {
    return 'MARCO';
  }
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [GameComponent],
  template: `
    <header>
      <h1>DOWNGRADE</h1>
      <ul class="status">
        <li [class]="api()">API Java: {{ api() }}</li>
        <li [class]="tools()">Tools Python: {{ tools() }}</li>
      </ul>
    </header>

    <main>
      <nav class="fases" aria-label="Fases">
        @for (f of fases; track f.numero) {
          <button type="button" [class.atual]="f.numero === faseAtual()" [disabled]="!f.mapa"
                  [title]="'Ato ' + f.ato + ' — ' + f.nome + (f.mapa ? '' : ' (sem mapa ainda)')"
                  (click)="escolherFase(f.numero, $event)">
            {{ f.numero }}<span>{{ f.nome }}</span>
          </button>
        }
      </nav>

      <div class="palco">
        <app-game (faseCompleta)="aoCompletar($event)" />

        @if (resultado(); as r) {
          <div class="overlay">
            <div class="painel">
              <h2>{{ r.nomeFase }}</h2>
              <p class="sub">COMPLETA</p>
              <div class="numeros">
                <div><span>{{ formatar(r.tempoMs) }}</span>tempo</div>
                <div><span>{{ r.mortes }}</span>mortes</div>
              </div>

              @if (!salvo()) {
                <form (submit)="salvar($event)">
                  <input [value]="nome()" (input)="nome.set($any($event.target).value)" maxlength="32"
                         placeholder="Seu nome" aria-label="Seu nome" />
                  <button type="submit" [disabled]="enviando() || !nome().trim()">Salvar no ranking</button>
                </form>
              }
              @if (erro()) { <p class="erro">{{ erro() }}</p> }

              <h3>Ranking</h3>
              <ol>
                @for (s of ranking(); track s.id) {
                  <li [class.eu]="s.id === meuId()">
                    <span>{{ s.player }}</span><span>{{ formatar(s.timeMs) }}</span><span>{{ s.deaths }}☠</span>
                  </li>
                } @empty {
                  <li class="vazio">Nenhum tempo ainda.</li>
                }
              </ol>

              <button class="jogar" (click)="jogarDeNovo()">Jogar de novo</button>
            </div>
          </div>
        }
      </div>
      <p class="help">A/D mover · W/Espaço pular · Clique/J atacar na direção do mouse · Q troca Espada/Canhão · Shift Overtime (drena vida) · R reiniciar</p>
    </main>
  `,
  styles: [`
    header { display: flex; align-items: center; justify-content: space-between; padding: 12px 24px; flex-wrap: wrap; gap: 8px; }
    h1 { margin: 0; font-size: 22px; letter-spacing: 6px; color: #00f0ff; text-shadow: 0 0 8px #00f0ff; }
    .status { list-style: none; display: flex; gap: 16px; margin: 0; padding: 0; font-size: 13px; }
    .online { color: #3dff9a; } .offline { color: #ff2a6d; } .verificando { color: #ffd166; }
    main { display: flex; flex-direction: column; align-items: center; padding: 0 16px; }
    .palco { position: relative; width: 100%; max-width: 960px; }
    .fases { display: flex; flex-wrap: wrap; gap: 6px; width: 100%; max-width: 960px; margin-bottom: 10px; }
    .fases button { flex: 1 1 0; min-width: 64px; background: #0d0221; color: #e8e6ff; border: 1px solid #3d2a5c; padding: 6px 8px;
                    font-size: 15px; text-align: left; }
    .fases button span { display: block; font-size: 10px; font-weight: normal; opacity: .7; white-space: nowrap;
                         overflow: hidden; text-overflow: ellipsis; }
    .fases button.atual { border-color: #00f0ff; color: #00f0ff; box-shadow: 0 0 10px #00f0ff55; }
    .fases button:disabled { opacity: .3; }
    .help { opacity: .7; font-size: 13px; text-align: center; }

    .overlay { position: absolute; inset: 0; display: grid; place-items: center; background: #07010fcc; overflow: auto; padding: 12px; }
    .painel { width: min(420px, 100%); background: #0d0221; border: 1px solid #ff2a6d; box-shadow: 0 0 24px #ff2a6d55; padding: 18px 22px; text-align: center; }
    h2 { margin: 0; color: #00f0ff; font-size: 18px; }
    .sub { margin: 2px 0 12px; color: #3dff9a; letter-spacing: 6px; font-size: 13px; }
    .numeros { display: flex; justify-content: center; gap: 32px; font-size: 12px; opacity: .9; }
    .numeros span { display: block; font-size: 24px; color: #e8e6ff; }
    form { display: flex; gap: 8px; margin: 14px 0 4px; }
    input { flex: 1; min-width: 0; background: #07010f; color: #e8e6ff; border: 1px solid #3d2a5c; padding: 8px; font: inherit; }
    button { background: #ff2a6d; color: #07010f; border: 0; padding: 8px 12px; font: inherit; font-weight: bold; cursor: pointer; }
    button:disabled { opacity: .5; cursor: default; }
    .jogar { margin-top: 12px; width: 100%; background: #00f0ff; }
    h3 { margin: 14px 0 6px; font-size: 13px; letter-spacing: 4px; color: #ffd166; }
    ol { margin: 0; padding: 0; list-style: none; font-size: 13px; text-align: left; counter-reset: pos; }
    li { display: grid; grid-template-columns: 1fr auto 3.5em; gap: 8px; padding: 3px 6px; counter-increment: pos; }
    li span:first-child::before { content: counter(pos) '. '; opacity: .6; }
    li.eu { background: #00f0ff22; color: #00f0ff; }
    li.vazio { display: block; opacity: .6; }
    .erro { color: #ff2a6d; font-size: 13px; }
  `],
})
export class AppComponent implements OnInit {
  private http = inject(HttpClient);
  private rankingService = inject(RankingService);
  private jogo = viewChild.required(GameComponent);

  readonly fases = FASES;
  faseAtual = signal(1);

  api = signal<Status>('verificando');
  tools = signal<Status>('verificando');

  resultado = signal<ResultadoFase | null>(null);
  ranking = signal<Score[]>([]);
  nome = signal(lerNome());
  salvo = signal(false);
  enviando = signal(false);
  erro = signal('');
  meuId = signal<number | null>(null);

  ngOnInit(): void {
    this.http.get('/api/health').subscribe({ next: () => this.api.set('online'), error: () => this.api.set('offline') });
    this.http.get('/tools/health').subscribe({ next: () => this.tools.set('online'), error: () => this.tools.set('offline') });
  }

  aoCompletar(r: ResultadoFase): void {
    this.resultado.set(r);
    this.salvo.set(false);
    this.erro.set('');
    this.meuId.set(null);
    this.carregarRanking(r.fase);
  }

  salvar(evento: Event): void {
    evento.preventDefault();
    const r = this.resultado();
    const nome = this.nome().trim();
    if (!r || !nome) return;

    try { localStorage.setItem(CHAVE_NOME, nome); } catch { /* sem storage, segue sem lembrar o nome */ }
    this.enviando.set(true);
    this.rankingService.enviar({ player: nome, level: r.fase, timeMs: r.tempoMs, deaths: r.mortes }).subscribe({
      next: (s) => {
        this.salvo.set(true);
        this.enviando.set(false);
        this.meuId.set(s.id);
        this.carregarRanking(r.fase);
      },
      error: () => {
        this.enviando.set(false);
        this.erro.set('Não foi possível salvar. A API Java está online?');
      },
    });
  }

  jogarDeNovo(): void {
    this.resultado.set(null);
    this.jogo().jogarFase(this.faseAtual());
  }

  escolherFase(numero: number, evento: Event): void {
    // Tira o foco do botao para Espaco (pulo) nao "clicar" nele de novo
    (evento.currentTarget as HTMLElement).blur();
    this.faseAtual.set(numero);
    this.resultado.set(null);
    this.jogo().jogarFase(numero);
  }

  formatar(ms: number): string {
    const s = ms / 1000;
    const min = Math.floor(s / 60);
    const seg = (s % 60).toFixed(2).padStart(5, '0');
    return `${min}:${seg}`;
  }

  private carregarRanking(fase: number): void {
    this.rankingService.top(fase).subscribe({
      next: (lista) => this.ranking.set(lista),
      error: () => this.ranking.set([]),
    });
  }
}
