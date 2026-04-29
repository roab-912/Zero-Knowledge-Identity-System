/**
 * Calcule Poseidon(a, b, ...) et imprime le résultat sur stdout.
 * Utilisation : node poseidon.js <a> <b> [...]
 *
 * Utilise circomlibjs pour garantir une compatibilité exacte avec
 * le template Poseidon de circomlib utilisé dans le circuit.
 */

const { buildPoseidon } = require("circomlibjs");

async function main() {
    const args = process.argv.slice(2);
    if (args.length === 0) {
        process.stderr.write("Usage: node poseidon.js <input1> <input2> [...]\n");
        process.exit(1);
    }

    const inputs = args.map(x => BigInt(x));
    const poseidon = await buildPoseidon();
    const hash = poseidon(inputs);
    const F = poseidon.F;

    process.stdout.write(F.toObject(hash).toString() + "\n");
}

main().catch(err => {
    process.stderr.write(err.message + "\n");
    process.exit(1);
});
