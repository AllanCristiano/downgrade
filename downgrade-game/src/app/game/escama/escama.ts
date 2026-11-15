/**
 * ESCAMA ZERO — o chip de comando que Marco encontra no cadaver do lixao.
 * Diferente das outras Escamas, ela absorve o poder das Escamas derrotadas.
 * Comeca so com a Espada nivel 0; Canhao e Overtime sao desbloqueados na historia.
 */
export type HabilidadeId = 'espada' | 'canhao' | 'overtime';

export interface Habilidade {
  id: HabilidadeId;
  nome: string;
  descricao: string;
  nivel: number;
  nivelMax: number;
  desbloqueada: boolean;
  /** Fase em que a habilidade e absorvida na historia. */
  desbloqueiaNaFase: number;
}

export class Escama {
  /** Pontos de "fragmento" ganhos ao absorver Escamas de inimigos. */
  fragmentos = 0;

  readonly habilidades: Record<HabilidadeId, Habilidade> = {
    espada: {
      id: 'espada',
      nome: 'Espada',
      descricao: 'Lâmina de plasma. Nível 0: curta e lenta. Upa até rebater balas e cortar escudos.',
      nivel: 0,
      nivelMax: 5,
      desbloqueada: true,
      desbloqueiaNaFase: 1,
    },
    canhao: {
      id: 'canhao',
      nome: 'Canhão',
      descricao: 'Absorvido do Rato (chefe da fase 3). Tiro de longo alcance que perfura inimigos.',
      nivel: 0,
      nivelMax: 4,
      desbloqueada: false,
      desbloqueiaNaFase: 3,
    },
    overtime: {
      id: 'overtime',
      nome: 'Overtime',
      descricao: 'Absorvido da Agente Vidro (chefe da fase 6). Tudo em câmera lenta, mas drena a vida de Marco.',
      nivel: 0,
      nivelMax: 4,
      desbloqueada: false,
      desbloqueiaNaFase: 6,
    },
  };

  tem(id: HabilidadeId): boolean {
    return this.habilidades[id].desbloqueada;
  }

  nivel(id: HabilidadeId): number {
    return this.habilidades[id].nivel;
  }

  /** Absorve a Escama de um chefe e desbloqueia a habilidade dele. */
  absorver(id: HabilidadeId): void {
    this.habilidades[id].desbloqueada = true;
  }

  /** Gasta 1 fragmento para subir o nivel de uma habilidade desbloqueada. */
  upar(id: HabilidadeId): boolean {
    const h = this.habilidades[id];
    if (!h.desbloqueada || h.nivel >= h.nivelMax || this.fragmentos < 1) return false;
    this.fragmentos--;
    h.nivel++;
    return true;
  }

  // ---- valores derivados do nivel (balanceamento) ----

  /** Alcance do corte da espada em px. */
  alcanceEspada(): number {
    return 40 + this.nivel('espada') * 10;
  }

  /** Vida drenada por segundo (tempo real) enquanto o Overtime esta ativo. */
  drenoOvertime(): number {
    return 25 - this.nivel('overtime') * 4;
  }

  /** Recarga do canhao em ms. */
  recargaCanhao(): number {
    return 600 - this.nivel('canhao') * 100;
  }
}
