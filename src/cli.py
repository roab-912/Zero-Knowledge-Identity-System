"""
Interface en ligne de commande du système d'identité ZK.

Commandes :
  register <username> <secret>   Enregistre une nouvelle identité
  prove    <username> <secret>   Génère une preuve ZK d'identité
  verify   <username>            Vérifie une preuve générée
  list                           Liste les identités enregistrées
"""

import argparse
import json
import sys
from pathlib import Path

from .crypto import poseidon, random_field_element, secret_to_field
from .identity_db import get_identity, list_identities, register_identity
from .prover import prove
from .verifier import verify

PROOFS_DIR = Path(__file__).parent.parent / "proofs"


def cmd_register(args: argparse.Namespace) -> None:
    secret_int = secret_to_field(args.secret)
    nullifier = random_field_element()

    print(f"[*] Calcul du commitment Poseidon pour '{args.username}'...")
    commitment = poseidon(secret_int, nullifier)

    register_identity(args.username, commitment, nullifier)

    print(f"[+] Identité enregistrée pour '{args.username}'")
    print(f"    Commitment : {commitment}")
    print(f"    Nullifier  : {nullifier}")
    print(f"    (Le secret n'est jamais stocké)")


def cmd_prove(args: argparse.Namespace) -> None:
    commitment, nullifier = get_identity(args.username)
    secret_int = secret_to_field(args.secret)

    print(f"[*] Génération de la preuve ZK pour '{args.username}'...")
    try:
        proof, public_signals = prove(secret_int, nullifier, commitment)
    except RuntimeError as e:
        print(f"[-] Échec : {e}", file=sys.stderr)
        sys.exit(1)

    PROOFS_DIR.mkdir(exist_ok=True)
    proof_file = PROOFS_DIR / f"{args.username}_proof.json"
    public_file = PROOFS_DIR / f"{args.username}_public.json"

    with open(proof_file, "w") as f:
        json.dump(proof, f, indent=2)
    with open(public_file, "w") as f:
        json.dump(public_signals, f, indent=2)

    print(f"[+] Preuve générée avec succès !")
    print(f"    Fichier preuve  : {proof_file}")
    print(f"    Signaux publics : {public_file}")
    print(f"    Commitment      : {public_signals[0]}")


def cmd_verify(args: argparse.Namespace) -> None:
    proof_file = PROOFS_DIR / f"{args.username}_proof.json"
    public_file = PROOFS_DIR / f"{args.username}_public.json"

    if not proof_file.exists():
        print(f"[-] Aucune preuve trouvée pour '{args.username}'. Exécutez d'abord 'prove'.")
        sys.exit(1)

    commitment, _ = get_identity(args.username)

    with open(proof_file) as f:
        proof = json.load(f)
    with open(public_file) as f:
        public_signals = json.load(f)

    print(f"[*] Vérification de la preuve pour '{args.username}'...")
    try:
        valid = verify(proof, public_signals, commitment)
    except RuntimeError as e:
        print(f"[-] Erreur : {e}", file=sys.stderr)
        sys.exit(1)

    if valid:
        print(f"[+] VALIDE — L'identité de '{args.username}' est prouvée sans révéler le secret.")
    else:
        print(f"[-] INVALIDE — La preuve est incorrecte ou ne correspond pas à '{args.username}'.")
        sys.exit(1)


def cmd_list(args: argparse.Namespace) -> None:
    identities = list_identities()
    if not identities:
        print("Aucune identité enregistrée.")
    else:
        print("Identités enregistrées :")
        for name in identities:
            print(f"  - {name}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="zkidentity",
        description="Système d'identité Zero-Knowledge (Circom / snarkjs / Groth16)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_reg = sub.add_parser("register", help="Enregistrer une nouvelle identité")
    p_reg.add_argument("username", help="Nom d'utilisateur")
    p_reg.add_argument("secret", help="Secret (mot de passe)")
    p_reg.set_defaults(func=cmd_register)

    p_prv = sub.add_parser("prove", help="Générer une preuve ZK d'identité")
    p_prv.add_argument("username", help="Nom d'utilisateur")
    p_prv.add_argument("secret", help="Secret (mot de passe)")
    p_prv.set_defaults(func=cmd_prove)

    p_ver = sub.add_parser("verify", help="Vérifier une preuve ZK")
    p_ver.add_argument("username", help="Nom d'utilisateur")
    p_ver.set_defaults(func=cmd_verify)

    sub.add_parser("list", help="Lister les identités enregistrées").set_defaults(func=cmd_list)

    args = parser.parse_args()
    try:
        args.func(args)
    except (KeyError, ValueError) as e:
        print(f"[-] {e}", file=sys.stderr)
        sys.exit(1)
