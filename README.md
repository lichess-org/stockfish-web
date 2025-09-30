## stockfish-web

stockfish wasms for use in lichess.org web analysis

## Building

```
# Example: Clean and make all web targets

./build.py all clean
```

use `--flags` to override the default emcc flags which are `-O3 -DNDEBUG --closure=1`. use `--node` to target the node runtime.

check `./build.py --help` for the latest targets

to avoid installing or changing your emscripten version, use `./build-with-docker.sh` or `./build-with-podman.sh`:

```
# Example: Docker clean and make all node targets as debug with SAFE_HEAP

./build-with-docker.sh --flags='-O0 -g3 -sSAFE_HEAP' --node all clean
```

`./build.py` downloads sources to the `./fishes` folder then applies diffs from the `./patches` folder.
Edit the Stockfish sources within `./fishes`. Contribute your edits via patch file

```
# Example: Update `sf171-7.patch` with your source changes:

  cd fishes/sf171-7
  git diff > ../../patches/sf171-7.patch
```

## Run locally on node

```
./build.py --node
node ./src/wasm-cli.js ./sf171-79.js
```

Now you'll have to load the nnues. (see `./src/wasm-cli.js`)

```
big nn-1c0000000000.nnue
small nn-37f18f62d772.nnue
```

_The specific file names might change, so check the output of `uci` for the correct names._

## Sources

### sf171-7 (Stockfish 17.1 linrock 256)

- repo: https://github.com/official-stockfish/Stockfish
- commit: [03e2748](https://github.com/official-stockfish/Stockfish/commit/03e27488f3d21d8ff4dbf3065603afa21dbd0ef3)
- tag: sf_17.1
- nnue: [nn-ecb35f70ff2a.nnue](https://tests.stockfishchess.org/api/nn/nn-ecb35f70ff2a.nnue)

### sf171-79 (Official Stockfish 17.1 release)

- repo: https://github.com/official-stockfish/Stockfish
- commit: [03e2748](https://github.com/official-stockfish/Stockfish/commit/03e27488f3d21d8ff4dbf3065603afa21dbd0ef3)
- tag: sf_17.1
- big nnue: [nn-1c0000000000.nnue](https://tests.stockfishchess.org/api/nn/nn-1c0000000000.nnue)
- small nnue: [nn-37f18f62d772.nnue](//tests.stockfishchess.org/api/nn/nn-37f18f62d772.nnue)

### fsf14 (Fairy-Stockfish 14)

- repo: https://github.com/fairy-stockfish/Fairy-Stockfish
- commit: [a621470](https://github.com/fairy-stockfish/Fairy-Stockfish/commit/a621470)
- nnues: see repo links
