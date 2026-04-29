"""
Génération de preuves ZK via snarkjs (Groth16).

Appelle : snarkjs groth16 fullprove input.json circuit.wasm circuit_final.zkey proof.json public.json
"""

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
CIRCUITS_DIR = ROOT / "circuits"

WASM_PATH = CIRCUITS_DIR / "circuit_js" / "circuit.wasm"
ZKEY_PATH = CIRCUITS_DIR / "circuit_final.zkey"


def prove(secret: int, nullifier: int, commitment: int) -> tuple[dict, list]:
    """
    Génère une preuve Groth16 prouvant que Poseidon(secret, nullifier) == commitment
    sans révéler secret ni nullifier.

    Retourne (proof, public_signals).
    """
    _check_files()

    input_data = {
        "secret": str(secret),
        "nullifier": str(nullifier),
        "commitment": str(commitment),
    }

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        input_path  = tmp / "input.json"
        proof_path  = tmp / "proof.json"
        public_path = tmp / "public.json"

        with open(input_path, "w") as f:
            json.dump(input_data, f)

        try:
            subprocess.run(
                [
                    "snarkjs", "groth16", "fullprove",
                    str(input_path),
                    str(WASM_PATH),
                    str(ZKEY_PATH),
                    str(proof_path),
                    str(public_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            raise RuntimeError("snarkjs introuvable. Installez-le : npm install -g snarkjs")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Génération de preuve échouée — secret incorrect ou circuit invalide.\n"
                f"Détail :\n{e.stderr.strip()}"
            )

        with open(proof_path) as f:
            proof = json.load(f)
        with open(public_path) as f:
            public_signals = json.load(f)

    return proof, public_signals


def _check_files() -> None:
    if not WASM_PATH.exists():
        raise FileNotFoundError(
            f"WASM introuvable : {WASM_PATH}\n"
            "Compilez le circuit : circom circuits/identity.circom --r1cs --wasm --sym -o circuits/ -l node_modules"
        )
    if not ZKEY_PATH.exists():
        raise FileNotFoundError(
            f"ZKey introuvable : {ZKEY_PATH}\n"
            "Attendu : circuits/circuit_final.zkey"
        )
