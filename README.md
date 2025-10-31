## stockfish-web

stockfish wasms for use in lichess.org web analysis

## Building

```
# Example: Clean and make all web targets

./build.py all clean
```

use `--cxx` to override the default emcc flags which are `-O3 -DNDEBUG --closure=1`.

use `--ld` to override default linker flags (`--ld='-sENVIRONMENT=node'` to target node).

check `./build.py --help` for the latest targets

to avoid installing or changing your emscripten version, use `./build-with-docker.sh` or `./build-with-podman.sh`:

```
# Example: Docker clean and make all targets for node as debug with SAFE_HEAP

./build-with-docker.sh --cxx='-O0 -g3 -sSAFE_HEAP' --ld='-sENVIRONMENT=node' all clean

# Example: clean and make dist targets for web with a preallocated pthread pool size of 8

./build.py --ld='-sENVIRONMENT=web,worker -sPTHREAD_POOL_SIZE=8' clean dist
```

`./build.py` downloads sources to the `./fishes` folder then applies diffs from the `./patches` folder.
Edit the Stockfish sources within `./fishes`. Contribute your edits via patch file

```
# Example: Update `sf17_1-7.patch` with your source changes:

  cd fishes/sf17_1-7
  git diff > ../../patches/sf17_1-7.patch
```

## Run locally on node

```
./build.py --node
node ./src/wasm-cli.js ./sf17_1-79.js
uci
```
Check the output of `uci` for the correct nnue names and download ones you don't have from https://tests.stockfishchess.org/nns

Now you'll have to load the nnues. (see `./src/wasm-cli.js`).

```
big nn-1c0000000000.nnue
small nn-37f18f62d772.nnue
```

_The specific file names might change, so check the output of `uci` for the correct names._

## Sources

### sf17_1-7 (Stockfish 17.1 linrock 256)

- repo: https://github.com/official-stockfish/Stockfish
- commit: [03e2748](https://github.com/official-stockfish/Stockfish/commit/03e27488f3d21d8ff4dbf3065603afa21dbd0ef3)
- tag: sf_17.1
- nnue: [nn-ecb35f70ff2a.nnue](https://tests.stockfishchess.org/api/nn/nn-ecb35f70ff2a.nnue)

### sf17_1-79 (Official Stockfish 17.1 release)

- repo: https://github.com/official-stockfish/Stockfish
- commit: [03e2748](https://github.com/official-stockfish/Stockfish/commit/03e27488f3d21d8ff4dbf3065603afa21dbd0ef3)
- tag: sf_17.1
- big nnue: [nn-1c0000000000.nnue](https://tests.stockfishchess.org/api/nn/nn-1c0000000000.nnue)
- small nnue: [nn-37f18f62d772.nnue](//tests.stockfishchess.org/api/nn/nn-37f18f62d772.nnue)

### fsf14 (Fairy-Stockfish 14)

- repo: https://github.com/fairy-stockfish/Fairy-Stockfish
- commit: [a621470](https://github.com/fairy-stockfish/Fairy-Stockfish/commit/a621470)
- nnues: see repo links
