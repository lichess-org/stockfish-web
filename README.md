# `@lichess-org/stockfish-web`

[![npmjs.com/package/@lichess-org/stockfish-web](https://img.shields.io/npm/v/%40lichess-org%2Fstockfish-web)](https://www.npmjs.com/package/@lichess-org/stockfish-web)

WebAssembly builds for Stockfish.

This package is optimized for the lichess.org website, which needs multiple builds and chess variants. It is not straight-forward to load and use.

Check out https://github.com/nmrugg/stockfish.js for a simpler browser Stockfish.

## Building

```
# Example: Clean and make all web targets
./build.py all clean
```

Use `--cxx` to override the default emcc flags which are `-O3 -DNDEBUG --closure=1`.

Use `--ld` to override default linker flags (`--ld='-sENVIRONMENT=node'` to target node).

Check `./build.py --help` for the latest targets

To avoid installing or changing your emscripten version, use `./build-with-docker.sh` or `./build-with-podman.sh`:

```
# Example: Docker clean and make all targets for node as debug with SAFE_HEAP
./build-with-docker.sh --cxx='-O0 -g3 -sSAFE_HEAP' --ld='-sENVIRONMENT=node' all clean

# Example: clean and make dist targets for web with a preallocated pthread pool size of 8
./build.py --ld='-sENVIRONMENT=web,worker -sPTHREAD_POOL_SIZE=8' clean dist
```

`./build.py` downloads sources to the `./fishes` folder then applies diffs from the `./patches` folder.
Edit the Stockfish sources within `./fishes`. Contribute your edits via patch file

```
# Example: Update `sf_17.1.patch` with your source changes:
cd fishes/sf_17.1
git diff > ../../patches/sf_17.1.patch
```

## Run locally on node

```
./build.py --ld='-sENVIRONMENT=node'
node ./src/wasm-cli.js ./sf_18.js
uci
```

Check the output of `uci` for the correct nnue names and download ones you don't have from https://tests.stockfishchess.org/nns

Now you'll have to load the nnues. (see `./src/wasm-cli.js`).

```
big ./nn-c288c895ea92.nnue
small ./nn-37f18f62d772.nnue
```

_The specific file names might change, so check the output of `uci` for the correct names._

## Sources

### sf_18_smallnet (Stockfish 18 with sscg13/threat-small)

- repo: https://github.com/official-stockfish/Stockfish
- commit: [cb3d4ee9](https://github.com/official-stockfish/Stockfish/commit/cb3d4ee9b47d0c5aae855b12379378ea1439675c)
- tag: sf_18 (patch includes rebase of https://github.com/sscg13/Stockfish/tree/threat-small)
- nnue: [nn-4ca89e4b3abf.nnue](https://tests.stockfishchess.org/api/nn/nn-4ca89e4b3abf.nnue)

### sf_18 (Stockfish 18)

- repo: https://github.com/official-stockfish/Stockfish
- commit: [cb3d4ee9](https://github.com/official-stockfish/Stockfish/commit/cb3d4ee9b47d0c5aae855b12379378ea1439675c)
- tag: sf_18
- big nnue: [nn-c288c895ea92.nnue](https://tests.stockfishchess.org/api/nn/nn-c288c895ea92.nnue)
- small nnue: [nn-37f18f62d772.nnue](https://tests.stockfishchess.org/api/nn/nn-37f18f62d772.nnue)

### sf_dev (Stockfish dev-20260204-fac506bd)

- repo: https://github.com/official-stockfish/Stockfish
- commit: [fac506bd](https://github.com/official-stockfish/Stockfish/commit/fac506bdf3f0ed46fd0823ff1ed592824f91aa5a)
- tag: stockfish-dev-20260204-fac506bd
- big nnue: [nn-3dd094f3dfcf.nnue](https://tests.stockfishchess.org/api/nn/nn-3dd094f3dfcf.nnue)
- small nnue: [nn-37f18f62d772.nnue](https://tests.stockfishchess.org/api/nn/nn-37f18f62d772.nnue)

### sf_17.1_smallnet (Stockfish 17.1 linrock 256)

- repo: https://github.com/official-stockfish/Stockfish
- commit: [03e2748](https://github.com/official-stockfish/Stockfish/commit/03e27488f3d21d8ff4dbf3065603afa21dbd0ef3)
- tag: sf_17.1
- nnue: [nn-9067e33176e8.nnue](https://tests.stockfishchess.org/api/nn/nn-9067e33176e8.nnue)

### sf_17.1 (Official Stockfish 17.1 release)

- repo: https://github.com/official-stockfish/Stockfish
- commit: [03e27488](https://github.com/official-stockfish/Stockfish/commit/03e27488f3d21d8ff4dbf3065603afa21dbd0ef3)
- tag: sf_17.1
- big nnue: [nn-1c0000000000.nnue](https://tests.stockfishchess.org/api/nn/nn-1c0000000000.nnue)
- small nnue: [nn-37f18f62d772.nnue](//tests.stockfishchess.org/api/nn/nn-37f18f62d772.nnue)

### fsf_14 (Fairy-Stockfish 14)

- repo: https://github.com/fairy-stockfish/Fairy-Stockfish
- commit: [a621470b](https://github.com/fairy-stockfish/Fairy-Stockfish/commit/a621470b91757699f935ba06d5f4bf48a60574b1)
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
