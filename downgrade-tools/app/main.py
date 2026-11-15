"""Downgrade Tools: ferramentas de level design."""
from typing import Any

from fastapi import FastAPI

from .validacao import validar_mapa

app = FastAPI(title="Downgrade Tools")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "tools"}


@app.post("/levels/validate")
def validate_level(level: dict[str, Any]) -> dict[str, Any]:
    """Valida um mapa do Tiled (JSON) com as mesmas regras do build do jogo."""
    return validar_mapa(level)
