"""
Vérification de preuves ZK via snarkjs (Groth16).

Appelle : snarkjs groth16 verify verification_key.json public.json proof.json
Succès  : la sortie contient "[INFO]  snarkJS: OK!"
"""

import json
import re
import subprocess
import tempfile
from pathlib import Path

_ANSI = re.compile(r"\x1b\[[0-9;]*m")

ROOT = Path(__file__).parent.parent
CIRCUITS_DIR = ROOT / "circuits"
VKEY_PATH    = CIRCUITS_DIR / "verification_key.json"


def verify(proof: dict, public_signals: list, expected_commitment: int) -> bool:
    """
    Vérifie une preuve Groth16.

    Contrôle également que le signal public (commitment) correspond à
    la valeur stockée pour cet utilisateur, empêchant la réutilisation
    d'une preuve valide d'un autre utilisateur.

    Retourne True si la preuve est valide, False sinon.
    """
    if not VKEY_PATH.exists():
        raise FileNotFoundError(
            f"Clé de vérification introuvable : {VKEY_PATH}\n"
            "Exportez-la : snarkjs zkey export verificationkey circuits/circuit_final.zkey circuits/verification_key.json"
        )

    # Le commitment dans la preuve doit correspondre à l'identité demandée
    if not public_signals or int(public_signals[0]) != expected_commitment:
        return False

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        proof_path  = tmp / "proof.json"
        public_path = tmp / "public.json"

        with open(proof_path, "w") as f:
            json.dump(proof, f)
        with open(public_path, "w") as f:
            json.dump(public_signals, f)

        try:
            result = subprocess.run(
                [
                    "snarkjs", "groth16", "verify",
                    str(VKEY_PATH),
                    str(public_path),
                    str(proof_path),
                ],
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            raise RuntimeError("snarkjs introuvable. Installez-le : npm install -g snarkjs")

    output = _ANSI.sub("", result.stdout + result.stderr)
    return result.returncode == 0 and "snarkJS: OK!" in output
