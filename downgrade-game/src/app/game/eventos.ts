/** Eventos que o Phaser emite para o Angular (via game.events). */
export const EVENTO_FASE_COMPLETA = 'fase-completa';

export interface ResultadoFase {
  fase: number;
  nomeFase: string;
  tempoMs: number;
  mortes: number;
}
