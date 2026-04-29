"""
Opérations cryptographiques côté Python.

Le hash Poseidon est délégué à circomlibjs via un sous-processus Node.js
pour garantir une compatibilité exacte avec le circuit Circom.
"""

import hashlib
import secrets
import subprocess
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"

# Champ scalaire BN128 (même que dans le circuit)
P = 21888242871839275222246405745257275088548364400416034343698204186575808495617


def poseidon(*inputs: int) -> int:
    """
    Calcule Poseidon(inputs) en appelant circomlibjs via Node.js.
    Produit exactement le même résultat que le template Poseidon de circomlib.
    """
    args = ["node", str(SCRIPTS_DIR / "poseidon.js")] + [str(x) for x in inputs]
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=True,
            cwd=str(SCRIPTS_DIR),
        )
    except FileNotFoundError:
        raise RuntimeError(
            "Node.js introuvable. Installez Node.js et exécutez : cd scripts && npm install"
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Erreur Poseidon (circomlibjs) :\n{e.stderr.strip()}\n"
            "Avez-vous exécuté : cd scripts && npm install ?"
        )
    return int(result.stdout.strip())


def random_field_element() -> int:
    """Génère un élément aléatoire uniforme dans le champ BN128."""
    while True:
        val = secrets.randbits(254)
        if val < P:
            return val


def secret_to_field(secret_str: str) -> int:
    """
    Convertit une chaîne secrète en élément de champ BN128 via SHA-256.
    Déterministe : le même secret produit toujours le même entier.
    """
    digest = hashlib.sha256(secret_str.encode("utf-8")).digest()
    return int.from_bytes(digest, "big") % P
