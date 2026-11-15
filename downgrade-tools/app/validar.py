"""CLI: valida todos os mapas de uma pasta. Sai com codigo 1 se algum tiver erro.

Uso: python -m app.validar <pasta-das-fases>
Roda no build do jogo (downgrade-game/Dockerfile): fase quebrada nao entra no jogo.
"""
import json
import sys
from pathlib import Path

from .validacao import validar_mapa


def main() -> int:
    pasta = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    arquivos = sorted(pasta.glob("fase-*.json"))
    if not arquivos:
        print(f"Nenhum mapa 'fase-*.json' em {pasta}")
        return 1

    falhou = False
    for arq in arquivos:
        try:
            mapa = json.loads(arq.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"✗ {arq.name}: não é um JSON válido ({e})")
            falhou = True
            continue

        r = validar_mapa(mapa, arq.parent)
        print(f"{'✓' if r['valid'] else '✗'} {arq.name}  {r['stats']}")
        for e in r["errors"]:
            print(f"    ERRO  {e}")
        for a in r["warnings"]:
            print(f"    aviso {a}")
        falhou |= not r["valid"]

    return 1 if falhou else 0


if __name__ == "__main__":
    sys.exit(main())
