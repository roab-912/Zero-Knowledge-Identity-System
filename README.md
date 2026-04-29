# Zero-Knowledge Identity System

A minimal demonstration of Zero-Knowledge Proofs applied to identity verification.  
A user can **prove they know a secret linked to a registered identity — without ever revealing that secret**.

Built with [Circom](https://docs.circom.io/) · [snarkjs](https://github.com/iden3/snarkjs) · Python 3

---

## What is Zero-Knowledge?

A Zero-Knowledge Proof (ZKP) is a cryptographic protocol where a **prover** convinces a **verifier** that a statement is true, without revealing any information beyond the truth of that statement.

### Properties

| Property | Meaning |
|---|---|
| **Completeness** | An honest prover with a valid secret can always generate an accepted proof |
| **Soundness** | It is computationally impossible to generate a valid proof with the wrong secret |
| **Zero-Knowledge** | The verifier learns nothing about the secret beyond the fact that it is correct |

---

## How this system works

### Cryptographic model

Identity is based on a **Poseidon hash commitment**:

```
commitment = Poseidon(secret, nullifier)
```

- **`secret`** — the user's password, never stored anywhere
- **`nullifier`** — a random field element generated at registration, stored alongside the commitment
- **`commitment`** — the public hash stored in the identity database

The Poseidon hash function is ZK-friendly (low constraint count), making it efficient inside arithmetic circuits.  
All arithmetic is performed modulo the BN128 scalar field prime:

```
p = 21888242871839275222246405745257275088548364400416034343698204186575808495617
```

### Workflow

```
REGISTER                          PROVE                        VERIFY
────────                          ─────                        ──────
secret ──┐                        secret ──┐                   proof.json ──┐
         ├─→ Poseidon ──→ commitment        ├─→ ZK circuit ──→              ├─→ snarkjs ──→ VALID / INVALID
nullifier┘   (stored)             nullifier┘   (Groth16)      public.json ──┘
                                                ↓
                                           proof.json
                                           public.json
                                      (commitment only)
```

1. **Register**: compute `commitment = Poseidon(secret, nullifier)` and store `{username → commitment, nullifier}`. The secret is never persisted.

2. **Prove**: given `secret` and `nullifier`, the Circom circuit checks that `Poseidon(secret, nullifier) == commitment`. snarkjs generates a Groth16 proof — a small file that encodes this fact without exposing the inputs.

3. **Verify**: anyone with the `proof.json`, `public.json` (containing only the commitment), and the verification key can confirm the proof is valid in milliseconds — without access to the secret.

---

## Circuit

Located in `circuits/identity.circom`:

```circom
template IdentityProof() {
    signal input secret;      // private
    signal input nullifier;   // private
    signal input commitment;  // public

    component hasher = Poseidon(2);
    hasher.inputs[0] <== secret;
    hasher.inputs[1] <== nullifier;

    commitment === hasher.out;
}

component main {public [commitment]} = IdentityProof();
```

The single constraint `commitment === hasher.out` is the entire security of the system.  
If the prover supplies the wrong secret, the witness generation fails — making it impossible to produce any proof.

---

## Project structure

```
├── circuits/
│   ├── identity.circom         # ZK circuit (Circom 2.0)
│   ├── circuit.wasm            # compiled circuit (generated)
│   ├── circuit_final.zkey      # proving key (trusted setup)
│   └── verification_key.json   # verification key
├── scripts/
│   ├── package.json            # Node.js deps (circomlibjs)
│   └── poseidon.js             # Poseidon helper called by Python
├── src/
│   ├── crypto.py               # Poseidon hash + field utilities
│   ├── identity_db.py          # JSON identity store
│   ├── prover.py               # snarkjs fullprove wrapper
│   ├── verifier.py             # snarkjs verify wrapper
│   └── cli.py                  # CLI interface
├── data/
│   └── identities.json         # registered identities (gitignored)
├── proofs/                     # generated proofs (gitignored)
└── main.py                     # entry point
```

---

## Prerequisites

| Tool | Purpose | Install |
|---|---|---|
| Python 3.10+ | CLI and orchestration | [python.org](https://www.python.org/) |
| Node.js 16+ | Poseidon helper + snarkjs | [nodejs.org](https://nodejs.org/) |
| snarkjs | Proof generation and verification | `npm install -g snarkjs` |
| circom | Circuit compilation | [docs.circom.io](https://docs.circom.io/getting-started/installation/) |

No external Python packages are required (standard library only).

---

## Setup

### 1. Install Node.js dependencies

```bash
# circomlib — for circuit compilation
npm install circomlib

# circomlibjs — for Python's Poseidon helper
cd scripts && npm install && cd ..
```

### 2. Compile the circuit

```bash
circom circuits/identity.circom --r1cs --wasm --sym -o circuits/ -l node_modules
```

### 3. Trusted setup (Groth16)

```bash
# Download a Powers of Tau file (phase 1) — e.g. Hermez ceremony
snarkjs groth16 setup circuits/identity.r1cs pot12_final.ptau circuits/circuit_0000.zkey
snarkjs zkey contribute circuits/circuit_0000.zkey circuits/circuit_final.zkey --name="contributor"
snarkjs zkey export verificationkey circuits/circuit_final.zkey circuits/verification_key.json
```

---

## Usage

### Register an identity

```bash
python3 main.py register <username> <secret>
```

```
[*] Computing Poseidon commitment for 'alice'...
[+] Identity registered for 'alice'
    Commitment : 21713326775034767788564403041116518542224495836353285097146373941544449566841
    Nullifier  : 8354827152537005177856813016708110347122883790237928454175051007363662893192
    (The secret is never stored)
```

### Generate a proof

```bash
python3 main.py prove <username> <secret>
```

```
[*] Generating ZK proof for 'alice'...
[+] Proof generated successfully!
    Proof file      : proofs/alice_proof.json
    Public signals  : proofs/alice_public.json
    Commitment      : 21713326775034767788564403041116518542224495836353285097146373941544449566841
```

### Verify a proof

```bash
python3 main.py verify <username>
```

```
[*] Verifying proof for 'alice'...
[+] VALID — Identity of 'alice' proved without revealing the secret.
```

### Wrong secret — soundness in action

```bash
python3 main.py prove alice wrongsecret
# → ERROR: constraint not satisfied (line 24 of the circuit)
# → Impossible to generate a proof
```

The circuit itself rejects an incorrect secret at witness generation time.  
There is no valid proof to produce — this is the **soundness** guarantee of ZK.

### List registered identities

```bash
python3 main.py list
```

---

## What the verifier sees

The verifier only receives:
- `proof.json` — a Groth16 proof (~200 bytes of elliptic curve points)
- `public.json` — the commitment value, e.g. `["21713326..."]`

From these two files alone, the verifier confirms:

> *"Someone who knows a (secret, nullifier) pair whose Poseidon hash equals this commitment has produced this proof."*

The secret and nullifier remain completely hidden.

---

## Security notes

This project is a **demonstration**. For production use, consider:

- **Nullifier reuse**: the same nullifier is reused across proofs for the same identity. In production, nullifiers should be single-use to prevent linkability.
- **Trusted setup**: the Groth16 trusted setup requires at least one honest participant. Use a well-audited multi-party ceremony.
- **Secret entropy**: secrets are hashed with SHA-256 before entering the field, but low-entropy passwords remain vulnerable to offline dictionary attacks on the commitment.
- **Proof replay**: a valid proof for a given commitment can be replayed. Add a session challenge to the public inputs if replay protection is needed.
