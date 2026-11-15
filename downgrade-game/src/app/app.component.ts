import { Component, OnInit, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { GameComponent } from './game/game.component';

type Status = 'verificando' | 'online' | 'offline';

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
      <app-game />
      <p class="help">A/D mover · W/Espaço pular · J/clique Espada · K Canhão · Shift Overtime (drena vida) · R reiniciar</p>
    </main>
  `,
  styles: [`
    header { display: flex; align-items: center; justify-content: space-between; padding: 12px 24px; flex-wrap: wrap; gap: 8px; }
    h1 { margin: 0; font-size: 22px; letter-spacing: 6px; color: #00f0ff; text-shadow: 0 0 8px #00f0ff; }
    .status { list-style: none; display: flex; gap: 16px; margin: 0; padding: 0; font-size: 13px; }
    .online { color: #3dff9a; } .offline { color: #ff2a6d; } .verificando { color: #ffd166; }
    main { display: flex; flex-direction: column; align-items: center; padding: 0 16px; }
    .help { opacity: .7; font-size: 13px; text-align: center; }
  `],
})
export class AppComponent implements OnInit {
  private http = inject(HttpClient);
  api = signal<Status>('verificando');
  tools = signal<Status>('verificando');

  ngOnInit(): void {
    this.http.get('/api/health').subscribe({ next: () => this.api.set('online'), error: () => this.api.set('offline') });
    this.http.get('/tools/health').subscribe({ next: () => this.tools.set('online'), error: () => this.tools.set('offline') });
  }
}
