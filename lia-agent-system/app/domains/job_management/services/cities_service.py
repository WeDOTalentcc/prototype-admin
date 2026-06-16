"""
Onda 2B (audit 2026-06-06): busca de cidades global a partir de dataset estruturado.

Fonte: app/data/cities_br.json (IBGE completo, 5.571 municípios, com UF + país).
Plataforma global: novos países entram adicionando datasets/entradas (mesmo shape).
Autocomplete: busca accent-insensitive por substring no label, em memória (dataset pequeno).
"""
import json
import unicodedata
from functools import lru_cache
from pathlib import Path

_DATA_FILE = Path(__file__).resolve().parents[3] / "data" / "cities_br.json"


def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


@lru_cache(maxsize=1)
def _load() -> list[dict]:
    try:
        with open(_DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return []
    for c in data:
        c["_norm"] = _norm(c.get("label", ""))
    return data


def search_cities(query: str = "", limit: int = 50) -> list[dict]:
    """Busca cidades por substring (accent-insensitive). Vazio → primeiras `limit`.

    Retorna RemoteOption-like: {id, name, uf, country}. id == name (label) para
    round-trip no combobox + persistência como string canônica.
    """
    cities = _load()
    q = _norm(query)
    if q:
        matched = [c for c in cities if q in c["_norm"]][:limit]
    else:
        matched = cities[:limit]
    return [
        {"id": c["label"], "name": c["label"], "uf": c.get("uf"), "country": c.get("country")}
        for c in matched
    ]
