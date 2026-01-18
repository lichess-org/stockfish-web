#!/usr/bin/env python3
import argparse
import subprocess
import glob
import os
import os.path
import re

stockfish_repo = "https://github.com/official-stockfish/Stockfish"
fairy_stockfish_repo = "https://github.com/fairy-stockfish/Fairy-Stockfish"

# emscripten version requirements
MAJOR = 4
MINOR = 0
PATCH = 18

build_tags = ["all", "legacy", "dist"]

targets = {
    "fsf_14": {
        "url": fairy_stockfish_repo,
        "commit": "a621470b91757699f935ba06d5f4bf48a60574b1",
        "tags": ["all", "dist"],
    },
    "sf_17.1_smallnet": {
        "url": stockfish_repo,
        "commit": "03e27488f3d21d8ff4dbf3065603afa21dbd0ef3",
        "tags": ["all", "dist"],
    },
    "sf_17.1": {
        "url": stockfish_repo,
        "commit": "03e27488f3d21d8ff4dbf3065603afa21dbd0ef3",
        "tags": ["all", "dist"],
    },
}

default_target = "sf_17.1"

default_cxx_flags = [
  "-O3",
  "-DNDEBUG",
  "--closure=1",
]

default_ld_flags = [
    "-sENVIRONMENT=web,worker",
]

script_dir = os.path.dirname(os.path.realpath(__file__))
fishes_dir = os.path.join(script_dir, "fishes")
patches_dir = os.path.join(script_dir, "patches")

ignore_sources = [
    os.path.join("syzygy", "tbprobe.cpp"),
    "pyffish.cpp",
    "ffishjs.cpp",
]


def makefile(target, sources, cxx_flags, ld_flags):
    all_cxx_flags = " ".join(
        [cxx_flags.strip(), targets[target].get("cxx", "").strip()]
    )
    # DO NOT replace tabs with spaces
    # fmt: off
    return f"""

CXX = em++
EXE = {target}

CXX_FLAGS = {all_cxx_flags} -Isrc -pthread -msimd128 -mavx -flto -fno-exceptions \\
	-DUSE_POPCNT -DUSE_SSE2 -DUSE_SSSE3 -DUSE_SSE41 -DNO_PREFETCH -DNNUE_EMBEDDING_OFF

LD_FLAGS = {ld_flags} \\
	--pre-js=../../src/initModule.js -sEXIT_RUNTIME -sEXPORT_ES6 -sEXPORT_NAME={mod_name(target)} \\
	-sEXPORTED_FUNCTIONS='[_malloc,_main]' -sEXPORTED_RUNTIME_METHODS='[stringToUTF8,UTF8ToString,HEAPU8]' \\
	-sINCOMING_MODULE_JS_API='[locateFile,print,printErr,wasmMemory,buffer,instantiateWasm,mainScriptUrlOrBlob]' \\
	-sINITIAL_MEMORY=64MB -sALLOW_MEMORY_GROWTH -sSTACK_SIZE=3MB -sSTRICT -sPROXY_TO_PTHREAD \\
	-sALLOW_BLOCKING_ON_MAIN_THREAD=0 -Wno-pthreads-mem-growth

SRCS = {sources}
OBJS = $(addprefix src/, $(SRCS:.cpp=.o)) src/glue.o

$(EXE).js: $(OBJS)
	$(CXX) $(CXX_FLAGS) $(LD_FLAGS) $(OBJS) -o $(EXE).js

%.o: %.cpp
	$(CXX) $(CXX_FLAGS) -c $< -o $@

src/glue.o: ../../src/glue.cpp
	$(CXX) $(CXX_FLAGS) -c $< -o $@

"""


# fmt: on


def mod_name(target):
    return "_".join(seg.capitalize() for seg in re.split(r"[._-]", target)) + "_Web"


def main():
    parser = argparse.ArgumentParser(description="build stockfish wasms")
    parser.add_argument(
        "--cxx",
        help="em++ cxxflags. for debug use --cxx='-O0 -g3 -sSAFE_HEAP'. default: '%(default)s'",
        default=" ".join(default_cxx_flags),
    )
    parser.add_argument(
        "--ld",
        help="em++ linker flags. for node use --ld='-sENVIRONMENT=node'. default: '%(default)s'",
        default=" ".join(default_ld_flags),
    )
    parser.add_argument(
        "--emcc-version", action="store_true", help="print required emscripten version and exit"
    )
    parser.add_argument(
        "target",
        nargs="*",
        help=f"clean, {', '.join(build_tags + list(targets.keys()))}. default: '%(default)s'",
        default=[default_target],
    )

    args = parser.parse_args()
    if args.emcc_version:
        print(f"{MAJOR}.{MINOR}.{PATCH}")
        exit(0)

    arg_targets = list(args.target)
    if len(arg_targets) == 0:
        arg_targets = ["default"]

    if "clean" in arg_targets:
        clean()
        arg_targets.remove("clean")

    arg_targets = [
        name
        for tok in arg_targets
        for name in (
            [key for key, info in targets.items() if tok in info["tags"]]
            if tok in build_tags
            else [tok]
        )
    ]

    if len(arg_targets) > 0:
        assert_emsdk()
        print(f"building: {', '.join(arg_targets)}")
        print(f"cxxflags: {args.cxx}")
        print(f"ldflags: {args.ld}")
        print("")
    try:
        for target in arg_targets:
            build_target(target, args.cxx, args.ld)
    except Exception as e:
        print(e)


def build_target(target, cxx_flags, ld_flags):  # changes cwd
    target_dir = os.path.join(fishes_dir, target)
    fetch_sources(target)

    os.chdir(os.path.join(target_dir, "src"))

    sources = [
        f for f in glob.glob("**/*.cpp", recursive=True) if f not in ignore_sources
    ]

    os.chdir(target_dir)

    with open("Makefile.tmp", "w") as f:
        f.write(makefile(target, " ".join(sources), cxx_flags, ld_flags))

    subprocess.run(["make", "-f", "Makefile.tmp", "-j"], check=True)

    for f in [f"{target}.js", f"{target}.wasm"]:
        os.replace(os.path.join(target_dir, f), os.path.join(script_dir, f))


def fetch_sources(target):
    if target not in targets:
        raise Exception(f"unknown target: {target}")
    target_dir = os.path.join(fishes_dir, target)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        os.chdir(fishes_dir)
        env = os.environ | {
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "advice.detachedHead",
            "GIT_CONFIG_VALUE_0": "false",
        }
        subprocess.run(["git", "clone", targets[target]["url"], target], env=env, check=True)
        subprocess.run(
            ["git", "-C", target_dir, "checkout", targets[target]["commit"]], env=env, check=True
        )
        subprocess.run(
            [
                "git",
                "-C",
                target_dir,
                "apply",
                os.path.join(patches_dir, f"{target}.patch"),
            ],
            env=env,
            check=True,
        )


def clean():
    clean_list = glob.glob(f"{fishes_dir}/**/*.o", recursive=True)
    for target in targets.keys():
        clean_list.append(os.path.join(fishes_dir, target, "Makefile.tmp"))
        clean_list.extend(
            os.path.join(script_dir, f"{target}.{ext}")
            for ext in ["js", "worker.js", "wasm", "js.map", "worker.js.map"]
        )

    subprocess.run(["rm", "-rf"] + clean_list)
    return


def assert_emsdk():
    try:
        result = subprocess.run(
            ["emcc", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if result.stderr:
            print("Error:", result.stderr)
            exit(1)

        version_match = re.search(r"([\d]+)\.([\d]+)\.([\d]+)", result.stdout)
        if version_match:
            major, minor, patch = version_match.groups()
            if (int(major), int(minor), int(patch)) < (MAJOR, MINOR, PATCH):
                print(f"emsdk {MAJOR}.{MINOR}.{PATCH} or later is required")
                exit(1)
            else:
                return
        else:
            print("could not determine emcc version")
            exit(1)
    except FileNotFoundError:
        print("emcc not installed or not found in the system path")
        exit(1)


if __name__ == "__main__":
    main()
