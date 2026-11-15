import { AfterViewInit, Component, ElementRef, NgZone, OnDestroy, ViewChild, inject } from '@angular/core';
import Phaser from 'phaser';
import { LixaoScene } from './scenes/lixao.scene';

@Component({
  selector: 'app-game',
  standalone: true,
  template: `<div #host class="game-host"></div>`,
  styles: [`
    .game-host { width: 100%; max-width: 960px; aspect-ratio: 16 / 9; border: 1px solid #2a1b3d; box-shadow: 0 0 24px #ff2a6d33; }
  `],
})
export class GameComponent implements AfterViewInit, OnDestroy {
  @ViewChild('host', { static: true }) host!: ElementRef<HTMLDivElement>;
  private zone = inject(NgZone);
  private game?: Phaser.Game;

  ngAfterViewInit(): void {
    // Roda o loop do Phaser fora do Angular para nao disparar change detection a cada frame
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
        scene: [LixaoScene],
      });
    });
  }

  ngOnDestroy(): void {
    this.game?.destroy(true);
  }
}
