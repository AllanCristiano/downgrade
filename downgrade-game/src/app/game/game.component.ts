import { AfterViewInit, Component, ElementRef, NgZone, OnDestroy, ViewChild, inject, output } from '@angular/core';
import Phaser from 'phaser';
import { EVENTO_FASE_COMPLETA, ResultadoFase } from './eventos';
import { DadosFase, FaseScene, REG_INICIO, REG_MORTES } from './scenes/fase.scene';

@Component({
  selector: 'app-game',
  standalone: true,
  template: `<div #host class="game-host"></div>`,
  styles: [`
    :host { display: block; width: 100%; }
    .game-host { width: 100%; aspect-ratio: 16 / 9; border: 1px solid #2a1b3d; box-shadow: 0 0 24px #ff2a6d33; }
  `],
})
export class GameComponent implements AfterViewInit, OnDestroy {
  @ViewChild('host', { static: true }) host!: ElementRef<HTMLDivElement>;
  readonly faseCompleta = output<ResultadoFase>();

  private zone = inject(NgZone);
  private game?: Phaser.Game;

  ngAfterViewInit(): void {
    // Loop do Phaser fora do Angular para nao disparar change detection a cada frame
    this.zone.runOutsideAngular(() => {
      this.game = new Phaser.Game({
        type: Phaser.AUTO,
        parent: this.host.nativeElement,
        width: 960,
        height: 540,
        backgroundColor: '#0d0221',
        pixelArt: true,
        physics: { default: 'arcade', arcade: { gravity: { x: 0, y: 1400 } } },
        scale: { mode: Phaser.Scale.FIT, autoCenter: Phaser.Scale.CENTER_BOTH },
        scene: [FaseScene],
      });
      this.game.events.on(EVENTO_FASE_COMPLETA, (r: ResultadoFase) => this.zone.run(() => this.faseCompleta.emit(r)));
    });
  }

  /** Comeca a fase do zero (tempo e mortes zerados). */
  jogarFase(fase: number): void {
    if (!this.game) return;
    this.game.registry.remove(REG_INICIO);
    this.game.registry.remove(REG_MORTES);
    this.game.scene.getScene('fase')?.scene.restart({ fase } satisfies DadosFase);
  }

  ngOnDestroy(): void {
    this.game?.destroy(true);
  }
}
