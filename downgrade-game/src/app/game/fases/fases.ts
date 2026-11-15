/**
 * As 9 fases de DOWNGRADE (ver docs/ROTEIRO.md).
 * `mapa` aponta para o JSON exportado do Tiled em public/assets/fases/.
 * Fases sem mapa ainda aparecem bloqueadas na selecao.
 */
export interface Fundo {
  url: string;
  /** Velocidade do parallax: 0 = parado no ceu, 1 = anda junto com a fase. */
  fator: number;
}

export interface InfoFase {
  numero: number;
  nome: string;
  ato: 'I — Sucata' | 'II — Cidade' | 'III — Ofídia';
  mapa?: string;
  /** Camadas de fundo, da mais distante para a mais proxima. */
  fundos?: Fundo[];
}

const FUNDOS_LIXAO: Fundo[] = [
  { url: 'assets/fundos/lixao-ceu.png', fator: 0 },
  { url: 'assets/fundos/lixao-cidade.png', fator: 0.15 },
  { url: 'assets/fundos/lixao-montes.png', fator: 0.4 },
];

export const FASES: InfoFase[] = [
  { numero: 1, nome: 'O Lixão', ato: 'I — Sucata', mapa: 'assets/fases/fase-1-lixao.json', fundos: FUNDOS_LIXAO },
  { numero: 2, nome: 'O Desmanche', ato: 'I — Sucata' },
  { numero: 3, nome: 'A Torre de Prensa', ato: 'I — Sucata' },
  { numero: 4, nome: 'Mercado Noturno', ato: 'II — Cidade' },
  { numero: 5, nome: 'Metrô Suspenso', ato: 'II — Cidade' },
  { numero: 6, nome: 'Clínica Ofídia', ato: 'II — Cidade' },
  { numero: 7, nome: 'A Fábrica de Escamas', ato: 'III — Ofídia' },
  { numero: 8, nome: 'O Servidor', ato: 'III — Ofídia' },
  { numero: 9, nome: 'O Topo da Torre', ato: 'III — Ofídia' },
];

export function infoFase(numero: number): InfoFase {
  const f = FASES.find((x) => x.numero === numero);
  if (!f?.mapa) throw new Error(`Fase ${numero} ainda não tem mapa.`);
  return f;
}

/**
 * Tilesets conhecidos: nome do tileset no Tiled -> imagem.
 * O nome no Tiled precisa ser igual a chave daqui (o validador Python tambem confere).
 */
export const TILESETS: Record<string, string> = {
  blocos: 'assets/tiles/blocos.png', // provisorio, para rascunhar fases
  lixao: 'assets/tiles/lixao.png',
};
