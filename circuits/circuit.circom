pragma circom 2.0.0;

// Compilation depuis le dossier racine :
//   circom circuits/identity.circom --r1cs --wasm --sym -o circuits/ -l node_modules
//
// Cela génère :
//   circuits/identity.r1cs
//   circuits/identity.sym
//   circuits/identity_js/identity.wasm

include "circomlib/circuits/poseidon.circom";

// Prouve la connaissance d'un (secret, nullifier) tel que
// Poseidon(secret, nullifier) == commitment (public).
template IdentityProof() {
    signal input secret;      // privé : connu uniquement du prouveur
    signal input nullifier;   // privé : aléatoire, lié à l'identité
    signal input commitment;  // public : stocké dans la base d'identités

    component hasher = Poseidon(2);
    hasher.inputs[0] <== secret;
    hasher.inputs[1] <== nullifier;

    commitment === hasher.out;
}

component main {public [commitment]} = IdentityProof();
