"""
Base de données locale des identités (fichier JSON).

Chaque entrée associe un nom d'utilisateur à :
  - commitment : Poseidon(secret, nullifier) — valeur publique
  - nullifier   : entier aléatoire généré à l'enregistrement — privé
"""

import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "identities.json"


def _load() -> dict:
    if not DB_PATH.exists():
        return {}
    with open(DB_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save(db: dict) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)


def register_identity(username: str, commitment: int, nullifier: int) -> None:
    db = _load()
    if username in db:
        raise ValueError(f"L'utilisateur '{username}' existe déjà.")
    db[username] = {
        "commitment": str(commitment),
        "nullifier": str(nullifier),
    }
    _save(db)


def get_identity(username: str) -> tuple[int, int]:
    """Retourne (commitment, nullifier) pour l'utilisateur donné."""
    db = _load()
    if username not in db:
        raise KeyError(f"Utilisateur '{username}' introuvable.")
    entry = db[username]
    return int(entry["commitment"]), int(entry["nullifier"])


def list_identities() -> list[str]:
    return list(_load().keys())
