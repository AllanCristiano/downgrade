import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Score {
  id: number;
  player: string;
  level: number;
  timeMs: number;
  deaths: number;
  createdAt: string;
}

export interface NovoScore {
  player: string;
  level: number;
  timeMs: number;
  deaths: number;
}

/** Ranking por fase, salvo no backend Java (downgrade-api). */
@Injectable({ providedIn: 'root' })
export class RankingService {
  private http = inject(HttpClient);

  top(fase: number): Observable<Score[]> {
    return this.http.get<Score[]>(`/api/scores/${fase}`);
  }

  enviar(score: NovoScore): Observable<Score> {
    return this.http.post<Score>('/api/scores', score);
  }
}
