"""Ferramentas de level design: valida mapas exportados do Tiled (JSON)."""
from typing import Any

from fastapi import FastAPI

app = FastAPI(title="Downgrade Tools")

# Camadas que toda fase precisa ter no Tiled (ver docs/ROTEIRO.md)
REQUIRED_TILE_LAYERS = {"solidos"}
REQUIRED_OBJECT_LAYERS = {"spawns"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "tools"}


@app.post("/levels/validate")
def validate_level(level: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    layers = level.get("layers")
    if not isinstance(layers, list):
        return {"valid": False, "errors": ["JSON nao parece um mapa do Tiled (sem 'layers')"], "warnings": []}

    tile_layers = {l.get("name") for l in layers if l.get("type") == "tilelayer"}
    object_layers = {l.get("name"): l for l in layers if l.get("type") == "objectgroup"}

    for name in REQUIRED_TILE_LAYERS - tile_layers:
        errors.append(f"Camada de tiles obrigatoria ausente: '{name}'")
    for name in REQUIRED_OBJECT_LAYERS - object_layers.keys():
        errors.append(f"Camada de objetos obrigatoria ausente: '{name}'")

    spawns = object_layers.get("spawns", {}).get("objects", [])
    marcos = [o for o in spawns if o.get("type", o.get("class")) == "marco"]
    enemies = [o for o in spawns if o.get("type", o.get("class")) in ("inimigo", "chefe")]

    if "spawns" in object_layers:
        if len(marcos) != 1:
            errors.append(f"A fase precisa de exatamente 1 spawn de 'marco' (encontrado {len(marcos)})")
        if not enemies:
            warnings.append("Nenhum inimigo ou chefe na fase")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "width": level.get("width"),
            "height": level.get("height"),
            "enemies": len(enemies),
        },
    }
