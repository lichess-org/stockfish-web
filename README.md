# `@lichess-org/stockfish-web`

[![npmjs.com/package/@lichess-org/stockfish-web](https://img.shields.io/npm/v/%40lichess-org%2Fstockfish-web)](https://www.npmjs.com/package/@lichess-org/stockfish-web)

WebAssembly builds for Stockfish.

This package is optimized for the lichess.org website, which needs multiple builds and chess variants. It is not straight-forward to load and use.

Check out https://github.com/nmrugg/stockfish.js for a simpler browser Stockfish.

## Building

`./build.py` downloads sources to the `./fishes` folder, applies diffs from the `./patches` folder,
and builds targets using local emsdk with a matching version, podman or docker.

```
# Example: Clean and make all targets with pgo and final bench signature verification
./build.py clean all --pgo --verify-bench

# Example: Clean and make dist targets for web with a preallocated pthread pool size of 8
./build.py --ld-flags='-sENVIRONMENT=web,worker -sPTHREAD_POOL_SIZE=8' clean dist
```

Use `--cxx-flags` to override the default emcc flags (`-O3 -DNDEBUG --closure=1`).

Use `--ld-flags` to override default linker flags (`--ld-flags='-sENVIRONMENT=web,worker,node'`).

Check `./build.py --help` for all available targets.

Edit the Stockfish sources within `./fishes`. Contribute your edits via patch file:

```
# Example: Update `sf_18.patch` with your commits
cd fishes/sf_18
git format-patch stockfish-web/base --stdout > ../../patches/sf_18.patch
```

## Run locally on node

`./tools/wasm-cli.ts` bootstraps the emscripten module and also automatically downloads the required
nnue files into the current working directory.

```
./build.py
node ./tools/wasm-cli.ts ./sf_18.js
uci
```

## Sources

### sf_18_smallnet (Stockfish 18 with sscg13/threat-small)

- repo: https://github.com/official-stockfish/Stockfish
- base: [cb3d4ee9](https://github.com/official-stockfish/Stockfish/commit/cb3d4ee9b47d0c5aae855b12379378ea1439675c)
- tag: sf_18 (patch includes rebase of https://github.com/sscg13/Stockfish/tree/threat-small)
- nnue: [nn-4ca89e4b3abf.nnue](https://tests.stockfishchess.org/api/nn/nn-4ca89e4b3abf.nnue)

### sf_18 (Stockfish 18)

- repo: https://github.com/official-stockfish/Stockfish
- base: [cb3d4ee9](https://github.com/official-stockfish/Stockfish/commit/cb3d4ee9b47d0c5aae855b12379378ea1439675c)
- tag: sf_18
- big nnue: [nn-c288c895ea92.nnue](https://tests.stockfishchess.org/api/nn/nn-c288c895ea92.nnue)
- small nnue: [nn-37f18f62d772.nnue](https://tests.stockfishchess.org/api/nn/nn-37f18f62d772.nnue)

### sf_dev (Stockfish dev-20260829-8bc5caa2)

- repo: https://github.com/official-stockfish/Stockfish
- base: [8bc5caa2](https://github.com/official-stockfish/Stockfish/commit/8bc5caa2e4b1d4c189b1428e93158b10d3edb0b6)
- tag: stockfish-dev-20260829-8bc5caa2
- nnue: [nn-1a298aa575a0.nnue](https://tests.stockfishchess.org/api/nn/nn-1a298aa575a0.nnue)

### fsf_14 (Fairy-Stockfish 14)

- repo: https://github.com/fairy-stockfish/Fairy-Stockfish
- base: [a621470b](https://github.com/fairy-stockfish/Fairy-Stockfish/commit/a621470b91757699f935ba06d5f4bf48a60574b1)
- nnues: see repo links

## Older repositories kept for compatibility

### [`stockfish-nnue.wasm`](https://github.com/hi-ogawa/Stockfish)

[![npmjs.com/package/stockfish-nnue.wasm](https://img.shields.io/npm/v/stockfish-nnue.wasm)](https://www.npmjs.com/package/stockfish-nnue.wasm)

Stockfish 14 without dynamic `import()` in WebWorker.

### [`stockfish.wasm`](https://github.com/lichess-org/stockfish.wasm) and `stockfish-mv.wasm`

[![npmjs.com/package/stockfish.wasm](https://img.shields.io/npm/v/stockfish.wasm)](https://www.npmjs.com/package/stockfish.wasm)
[![npmjs.com/package/stockfish-mv.wasm](https://img.shields.io/npm/v/stockfish-mv.wasm)](https://www.npmjs.com/package/stockfish-mv.wasm)

`SF_classical` (strongest handcoded eval) and multi-variant equivalent.
No SIMD. No dynamic `import()` in WebWorker.

### [`stockfish.js`](https://github.com/lichess-org/stockfish.js)

[![npmjs.com/package/stockfish.js](https://img.shields.io/npm/v/stockfish.js)](https://www.npmjs.com/package/stockfish.js)

Stockfish 10 in pure JavaScript or WebAssembly without shared memory.
