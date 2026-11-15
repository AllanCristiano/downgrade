"""Regras de validacao dos mapas de fase exportados do Tiled (JSON).

So usa a biblioteca padrao: roda tanto na API (FastAPI) quanto no build do jogo (CLI).
Regras espelham o que a cena do Phaser espera (downgrade-game/src/app/game/scenes/fase.scene.ts).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

TAMANHO_TILE = 32
CAMADA_SOLIDOS = "solidos"
CAMADA_SPAWNS = "spawns"
CAMADA_DECORACAO = "decoracao"  # opcional, sem colisao
CAMADA_ANIMADOS = "animados"    # opcional: objetos animados com luz
ANIMADOS_CONHECIDOS = {"neon", "barril_fogo", "poste", "tv", "barril_toxico"}

# Tilesets registrados no jogo (downgrade-game/src/app/game/fases/fases.ts -> TILESETS)
TILESETS_CONHECIDOS = {"blocos", "lixao"}

INIMIGOS = {"catador", "pistoleiro", "chefe"}
SPAWNS_CONHECIDOS = {"marco", "saida"} | INIMIGOS


def _tipo(obj: dict[str, Any]) -> str:
    return str(obj.get("type") or obj.get("class") or "").strip().lower()


def validar_mapa(mapa: dict[str, Any], pasta_mapa: Path | None = None) -> dict[str, Any]:
    """Valida um mapa. `pasta_mapa` (opcional) permite conferir se a imagem do tileset existe."""
    erros: list[str] = []
    avisos: list[str] = []

    camadas = mapa.get("layers")
    if not isinstance(camadas, list):
        return {"valid": False, "errors": ["JSON não parece um mapa do Tiled (sem 'layers')."], "warnings": [], "stats": {}}

    # ---- mapa ----
    if mapa.get("infinite"):
        erros.append("Mapa infinito não é suportado: em Map > Map Properties desmarque 'Infinite'.")
    if mapa.get("orientation") != "orthogonal":
        erros.append("Orientação precisa ser 'orthogonal'.")
    if mapa.get("tilewidth") != TAMANHO_TILE or mapa.get("tileheight") != TAMANHO_TILE:
        erros.append(f"Tiles precisam ser {TAMANHO_TILE}x{TAMANHO_TILE}.")

    largura = int(mapa.get("width") or 0)
    altura = int(mapa.get("height") or 0)

    # ---- tilesets ----
    for ts in mapa.get("tilesets", []):
        if "source" in ts:
            erros.append(
                f"Tileset externo '{ts['source']}': o Phaser só lê tilesets embutidos. "
                "No Tiled, abra o mapa e clique em 'Embed Tileset' no painel de Tilesets."
            )
            continue
        nome = ts.get("name")
        if nome not in TILESETS_CONHECIDOS:
            erros.append(f"Tileset '{nome}' não está registrado no jogo (conhecidos: {', '.join(sorted(TILESETS_CONHECIDOS))}).")
        if pasta_mapa is not None and ts.get("image"):
            if not (pasta_mapa / ts["image"]).resolve().is_file():
                erros.append(f"Imagem do tileset '{nome}' não encontrada: {ts['image']}")

    # ---- camadas ----
    por_nome = {c.get("name"): c for c in camadas}
    solidos = por_nome.get(CAMADA_SOLIDOS)
    spawns = por_nome.get(CAMADA_SPAWNS)

    grade: list[int] | None = None
    if not solidos or solidos.get("type") != "tilelayer":
        erros.append(f"Falta a camada de tiles '{CAMADA_SOLIDOS}'.")
    elif solidos.get("encoding") or solidos.get("compression"):
        erros.append(f"Camada '{CAMADA_SOLIDOS}': use o formato de camada 'CSV' (Map Properties > Tile Layer Format).")
    else:
        grade = solidos.get("data")

    deco = por_nome.get(CAMADA_DECORACAO)
    if deco is not None:
        if deco.get("type") != "tilelayer":
            erros.append(f"'{CAMADA_DECORACAO}' precisa ser uma camada de tiles.")
        elif deco.get("encoding") or deco.get("compression"):
            erros.append(f"Camada '{CAMADA_DECORACAO}': use o formato de camada 'CSV'.")

    animados = por_nome.get(CAMADA_ANIMADOS)
    if animados is not None:
        if animados.get("type") != "objectgroup":
            erros.append(f"'{CAMADA_ANIMADOS}' precisa ser uma camada de objetos.")
        else:
            for o in animados.get("objects", []):
                if _tipo(o) not in ANIMADOS_CONHECIDOS:
                    erros.append(f"animado #{o.get('id')} ('{_tipo(o)}'): classe desconhecida. Use: {', '.join(sorted(ANIMADOS_CONHECIDOS))}.")

    if not spawns or spawns.get("type") != "objectgroup":
        erros.append(f"Falta a camada de objetos '{CAMADA_SPAWNS}'.")
        objetos: list[dict[str, Any]] = []
    else:
        objetos = spawns.get("objects", [])

    # ---- spawns ----
    contagem: dict[str, int] = {}
    for o in objetos:
        tipo = _tipo(o)
        contagem[tipo] = contagem.get(tipo, 0) + 1
        rotulo = f"objeto #{o.get('id')} ('{tipo or 'sem classe'}')"

        if tipo not in SPAWNS_CONHECIDOS:
            erros.append(f"{rotulo}: classe desconhecida. Use: {', '.join(sorted(SPAWNS_CONHECIDOS))}.")
            continue

        x = float(o.get("x", 0)) + float(o.get("width", 0)) / 2
        base = float(o.get("y", 0)) + float(o.get("height", 0))
        col, lin = int(x // TAMANHO_TILE), int((base - 1) // TAMANHO_TILE)

        if not (0 <= col < largura and 0 <= lin < altura):
            erros.append(f"{rotulo}: está fora do mapa.")
        elif grade and grade[lin * largura + col] != 0 and tipo != "saida":
            erros.append(f"{rotulo}: está dentro de um bloco sólido (coluna {col}, linha {lin}).")

        if tipo == "catador":
            props = {p.get("name"): p.get("value") for p in o.get("properties", [])}
            patrulha = props.get("patrulha", 80)
            if not isinstance(patrulha, (int, float)) or patrulha < 0:
                erros.append(f"{rotulo}: 'patrulha' precisa ser um número >= 0.")

    if contagem.get("marco", 0) != 1:
        erros.append(f"A fase precisa de exatamente 1 'marco' (encontrado {contagem.get('marco', 0)}).")
    if contagem.get("saida", 0) != 1:
        erros.append(f"A fase precisa de exatamente 1 'saida' (encontrado {contagem.get('saida', 0)}).")

    total_inimigos = sum(contagem.get(t, 0) for t in INIMIGOS)
    if total_inimigos == 0:
        avisos.append("Nenhum inimigo na fase: a saída abre imediatamente.")

    nome_fase = next((p.get("value") for p in mapa.get("properties", []) if p.get("name") == "nome"), None)
    if not nome_fase:
        avisos.append("Mapa sem a propriedade 'nome' (Map > Map Properties).")

    return {
        "valid": not erros,
        "errors": erros,
        "warnings": avisos,
        "stats": {
            "nome": nome_fase,
            "largura_px": largura * TAMANHO_TILE,
            "altura_px": altura * TAMANHO_TILE,
            "inimigos": {t: contagem[t] for t in sorted(INIMIGOS) if t in contagem},
        },
    }
