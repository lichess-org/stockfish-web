#!/usr/bin/env python3

import argparse
import dataclasses
import subprocess
import glob
import os
import os.path
import re
import sys

from pathlib import Path
from typing import Iterable, Literal, NewType


stockfish_repo = "https://github.com/official-stockfish/Stockfish"
fairy_stockfish_repo = "https://github.com/fairy-stockfish/Fairy-Stockfish"

emcc_version_min = (4, 0, 18)
emcc_version_max = (6, 0, 0)

TargetName = NewType("TargetName", str)
Tag = Literal["all", "legacy", "dist"]

default_cxx_flags = [
  "-O3",
  "-DNDEBUG",
  "--closure=1",
]

default_ld_flags = [
    "-sENVIRONMENT=web,worker",
]

script_dir = Path(__file__).resolve().parent
fishes_dir = script_dir / "fishes"
patches_dir = script_dir / "patches"


@dataclasses.dataclass
class Target:
    repo: str
    commit: str
    patch: str
    tags: list[Tag]
    cxx_flags: list[str] = dataclasses.field(default_factory=list)

    def patch_path(self) -> Path:
        return patches_dir / self.patch


targets: dict[TargetName, Target] = {
    TargetName("fsf_14"): Target(
        repo=fairy_stockfish_repo,
        commit="a621470b91757699f935ba06d5f4bf48a60574b1",
        patch="fsf_14.patch",
        tags=["all", "dist"],
    ),
    TargetName("sf_17.1_smallnet"): Target(
        repo=stockfish_repo,
        commit="03e27488f3d21d8ff4dbf3065603afa21dbd0ef3",
        patch="sf_17.1_smallnet.patch",
        tags=["all", "legacy"],
    ),
    TargetName("sf_17.1"): Target(
        repo=stockfish_repo,
        commit="03e27488f3d21d8ff4dbf3065603afa21dbd0ef3",
        patch="sf_17.1.patch",
        tags=["all", "legacy"],
    ),
    TargetName("sf_18_smallnet"): Target(
        repo=stockfish_repo,
        commit="cb3d4ee9b47d0c5aae855b12379378ea1439675c",
        patch="sf_18_smallnet.patch",
        tags=["all", "dist"],
    ),
    TargetName("sf_18"): Target(
        repo=stockfish_repo,
        commit="cb3d4ee9b47d0c5aae855b12379378ea1439675c",
        patch="sf_18.patch",
        tags=["all", "dist"],
    ),
    TargetName("sf_dev"): Target(
        repo=stockfish_repo,
        commit="77d46ff61c3e33f7e9c1ef1f1b48315f23b04e80",
        patch="sf_dev.patch",
        tags=["all", "dist"],
    ),
}

relaxed_simd_cxx_flags = ["-mrelaxed-simd"]
targets[TargetName("sf_17.1_smallnet_relaxed-simd")] = dataclasses.replace(targets[TargetName("sf_17.1_smallnet")], cxx_flags=relaxed_simd_cxx_flags)
targets[TargetName("sf_17.1_relaxed-simd")] = dataclasses.replace(targets[TargetName("sf_17.1")], cxx_flags=relaxed_simd_cxx_flags)
targets[TargetName("sf_18_smallnet_relaxed-simd")] = dataclasses.replace(targets[TargetName("sf_18_smallnet")], cxx_flags=relaxed_simd_cxx_flags)
targets[TargetName("sf_18_relaxed-simd")] = dataclasses.replace(targets[TargetName("sf_18")], cxx_flags=relaxed_simd_cxx_flags)
targets[TargetName("sf_dev_relaxed-simd")] = dataclasses.replace(targets[TargetName("sf_dev")], cxx_flags=relaxed_simd_cxx_flags)

default_target = TargetName("sf_18_smallnet")

ignore_sources = [
    os.path.join("syzygy", "tbprobe.cpp"),
    "pyffish.cpp",
    "ffishjs.cpp",
]


def makefile(name: TargetName, sources: list[str], cxx_flags: str, ld_flags: str) -> str:
    target = targets[name]

    all_cxx_flags = " ".join([cxx_flags.strip(), *target.cxx_flags])

    # DO NOT replace tabs with spaces
    # fmt: off
    return f"""

CXX = em++
EXE = {name}

CXX_FLAGS = {all_cxx_flags} -Isrc -pthread -msimd128 -mavx -flto -fno-exceptions \\
	-DUSE_POPCNT -DUSE_SSE2 -DUSE_SSSE3 -DUSE_SSE41 -DNO_PREFETCH -DNNUE_EMBEDDING_OFF

LD_FLAGS = {ld_flags} \\
	--pre-js=../../src/initModule.js -sEXIT_RUNTIME -sEXPORT_ES6 -sEXPORT_NAME={mod_name(name)} \\
	-sEXPORTED_FUNCTIONS='[_malloc,_main]' -sEXPORTED_RUNTIME_METHODS='[stringToUTF8,UTF8ToString,HEAPU8]' \\
	-sINCOMING_MODULE_JS_API='[locateFile,print,printErr,wasmMemory,buffer,instantiateWasm,mainScriptUrlOrBlob]' \\
	-sINITIAL_MEMORY=64MB -sALLOW_MEMORY_GROWTH -sSTACK_SIZE=3MB -sSTRICT -sPROXY_TO_PTHREAD \\
	-sALLOW_BLOCKING_ON_MAIN_THREAD=0 -Wno-pthreads-mem-growth

SRCS = {' '.join(str(s) for s in sources)}
OBJS = $(addprefix src/, $(SRCS:.cpp=.o)) src/glue.o

$(EXE).js: $(OBJS)
	$(CXX) $(CXX_FLAGS) $(LD_FLAGS) $(OBJS) -o $(EXE).js

%.o: %.cpp
	$(CXX) $(CXX_FLAGS) -c $< -o $@

src/glue.o: ../../src/glue.cpp
	$(CXX) $(CXX_FLAGS) -c $< -o $@

"""
    # fmt: on


def mod_name(name: TargetName) -> str:
    return "_".join(seg.capitalize() for seg in re.split(r"[._-]", name)) + "_Web"


def join_version(version: Iterable[int]) -> str:
    return ".".join(str(v) for v in version)


def main() -> None:
    parser = argparse.ArgumentParser(description="build stockfish wasms")
    parser.add_argument(
        "--cxx-flags",
        help="em++ cxxflags. for debug use --cxx-flags='-O0 -g3 -sSAFE_HEAP'. default: '%(default)s'",
        default=" ".join(default_cxx_flags),
    )
    parser.add_argument(
        "--ld-flags",
        help="em++ linker flags. for node use --ld-flags='-sENVIRONMENT=node'. default: '%(default)s'",
        default=" ".join(default_ld_flags),
    )
    parser.add_argument(
        "--emcc-version", action="store_true", help="print required emscripten version and exit"
    )
    parser.add_argument(
        "targets",
        nargs="*",
        choices=["clean", *set(tag for info in targets.values() for tag in info.tags), *targets.keys()],
        default=default_target,
    )

    args = parser.parse_args()

    if args.emcc_version:
        print(join_version(emcc_version_min))
        sys.exit(0)

    if "clean" in args.targets:
        clean()

    selected_targets = [
        name
        for name, target in targets.items()
        if name in args.targets or any(tag in args.targets for tag in target.tags)
    ]

    if selected_targets:
        assert_emsdk()
        print(f"selected targets: {', '.join(selected_targets)}")
        print(f"cxx flags: {args.cxx_flags}")
        print(f"ld flags: {args.ld_flags}")

    for name in selected_targets:
        print("")
        print(f"# {name}")
        build_target(name, args.cxx_flags, args.ld_flags)


def build_target(name: TargetName, cxx_flags: str, ld_flags: str) -> None:
    fetch_sources(name)

    target_dir = fishes_dir / name

    sources = [
        f
        for f in glob.glob("**/*.cpp", root_dir=target_dir / "src", recursive=True)
        if f not in ignore_sources
    ]

    with open(target_dir / "Makefile.tmp", "w") as f:
        f.write(makefile(name, sources, cxx_flags, ld_flags))

    subprocess.check_call(["make", "-f", "Makefile.tmp", "-j"], cwd=target_dir)

    for asset in [f"{name}.js", f"{name}.wasm"]:
        (target_dir / asset).replace(script_dir / asset)


def fetch_sources(name: TargetName) -> None:
    target = targets[name]
    checkout_dir = fishes_dir / name

    try:
        checkout_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        print(f"skipping clone and patch for {name} (already exists)")
        return

    env = os.environ | {
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "advice.detachedHead",
        "GIT_CONFIG_VALUE_0": "false",
    }
    subprocess.check_call(["git", "clone", target.repo, name], env=env, cwd=fishes_dir)
    subprocess.check_call(["git", "checkout", target.commit], env=env, cwd=checkout_dir)
    subprocess.check_call(["git", "apply", target.patch_path()], env=env, cwd=checkout_dir)


def clean() -> None:
    clean_list = [
        *fishes_dir.glob("**/*.o"),
        *fishes_dir.glob("*/Makefile.tmp"),
        *[script_dir / f"{name}.{ext}" for name in targets.keys() for ext in ["js", "worker.js", "wasm", "js.map", "worker.js.map"]],
    ]

    for path in clean_list:
        path.unlink(missing_ok=True)


def assert_emsdk() -> None:
    try:
        stdout = subprocess.check_output(["emcc", "--version"], text=True)
    except FileNotFoundError:
        print("emcc not installed or not found in the system path")
        sys.exit(1)

    version_match = re.search(r"([\d]+)\.([\d]+)\.([\d]+)", stdout)
    if not version_match:
        print("could not determine emcc version")
        sys.exit(1)

    emcc_version = tuple(int(g) for g in version_match.groups())
    if not (emcc_version_min <= emcc_version < emcc_version_max):
        print(f"got emsdk {join_version(emcc_version)}, required >={join_version(emcc_version_min)},<{join_version(emcc_version_max)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
