#!/usr/bin/env python3

import argparse
import dataclasses
import functools
import glob
import os
import os.path
import re
import shlex
import shutil
import subprocess
import sys
import threading
from collections.abc import Iterable
from pathlib import Path
from typing import Literal

stockfish_repo = "https://github.com/official-stockfish/Stockfish"
fairy_stockfish_repo = "https://github.com/fairy-stockfish/Fairy-Stockfish"

TargetName = str
Tag = Literal["all", "legacy", "dist"]

default_cxx_flags = [
    "-O3",
    "-DNDEBUG",
    "--closure=1",
]

default_ld_flags = [
    "-sENVIRONMENT=web,worker,node",
]

script_dir = Path(__file__).resolve().parent
fishes_dir = script_dir / "fishes"
patches_dir = script_dir / "patches"
emsdk_cache_dir = script_dir / ".emsdk_cache"


@dataclasses.dataclass
class Target:
    repo: str
    commit: str
    patches: list[str]
    tags: list[Tag]
    emcc: tuple[int, int, int]
    cxx_flags: list[str] = dataclasses.field(default_factory=list)

    def relaxed_simd(self) -> "Target":
        return dataclasses.replace(self, cxx_flags=["-mrelaxed-simd", *self.cxx_flags])


targets: dict[TargetName, Target] = {
    "fsf_14": Target(
        repo=fairy_stockfish_repo,
        commit="a621470b91757699f935ba06d5f4bf48a60574b1",
        patches=["fsf_14.patch"],
        emcc=(5, 0, 7),
        tags=["all", "dist"],
    ),
    "sf_18_smallnet": Target(
        repo=stockfish_repo,
        commit="cb3d4ee9b47d0c5aae855b12379378ea1439675c",
        patches=["sf_18_smallnet.patch"],
        emcc=(5, 0, 7),
        tags=["all", "dist"],
    ),
    "sf_18": Target(
        repo=stockfish_repo,
        commit="cb3d4ee9b47d0c5aae855b12379378ea1439675c",
        patches=["sf_18.patch"],
        emcc=(5, 0, 7),
        tags=["all", "dist"],
    ),
    "sf_dev": Target(
        repo=stockfish_repo,
        commit="415ff793a09ec8d029b6253c0eba4c8c106e61e7",
        patches=["sf_dev.patch"],
        emcc=(6, 0, 5),
        tags=["all", "dist"],
    ),
}
targets["sf_18_smallnet_relaxed-simd"] = targets["sf_18_smallnet"].relaxed_simd()
targets["sf_18_relaxed-simd"] = targets["sf_18"].relaxed_simd()
targets["sf_dev_relaxed-simd"] = targets["sf_dev"].relaxed_simd()

default_target = "all"

ignore_sources = [
    os.path.join("universal", "entry_arm64.cpp"),
    os.path.join("universal", "entry_x86.cpp"),
    os.path.join("universal", "entry_riscv64.cpp"),
    os.path.join("universal", "nnue_embed.cpp"),
    "pyffish.cpp",
    "ffishjs.cpp",
]


def makefile(
    name: TargetName, sources: list[str], cxx_flags: str, ld_flags: str
) -> str:
    target = targets[name]

    all_cxx_flags = " ".join([cxx_flags.strip(), *target.cxx_flags])

    # DO NOT replace tabs with spaces
    # fmt: off
    return f"""

CXX = em++
EXE = {name}

CXX_FLAGS = {all_cxx_flags} -Isrc -pthread -msimd128 -mavx -flto -fno-exceptions \\
	-DUSE_POPCNT -DUSE_SSE2 -DUSE_SSSE3 -DUSE_SSE41 -DNO_PREFETCH \\
	-DNNUE_EMBEDDING_OFF -DNO_TABLEBASES \\
	-DSTOCKFISH_WEB_{name.upper().replace("-", "_")}

LD_FLAGS = {ld_flags} \\
	--pre-js=../../src/initModule.js -sEXIT_RUNTIME -sEXPORT_ES6 -sEXPORT_NAME={mod_name(name)} \\
	-sEXPORTED_FUNCTIONS='[_malloc,_main]' -sEXPORTED_RUNTIME_METHODS='[stringToUTF8,UTF8ToString,HEAPU8]' \\
	-sINCOMING_MODULE_JS_API='[locateFile,print,printErr,wasmMemory,buffer,instantiateWasm,mainScriptUrlOrBlob,onExit]' \\
	-sINITIAL_MEMORY=64MB -sALLOW_MEMORY_GROWTH -sSTACK_SIZE=3MB -sSTRICT -sPROXY_TO_PTHREAD \\
	-sALLOW_BLOCKING_ON_MAIN_THREAD=0 -Wno-pthreads-mem-growth

SRCS = {' '.join(str(s) for s in sources)}
OBJS = $(addprefix src/, $(SRCS:.cpp=.o)) src/glue.o

$(EXE).js: $(OBJS)
	$(CXX) $(CXX_FLAGS) $(LD_FLAGS) $(OBJS) -o $(EXE).js

$(OBJS): Makefile.tmp

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
        help="em++ linker flags. default: '%(default)s'",
        default=" ".join(default_ld_flags),
    )
    parser.add_argument(
        "--pgo",
        action="store_true",
        help="profile guided optimization: build instrumented, collect profile by running bench, rebuild using the profile",
    )
    parser.add_argument(
        "--verify-bench",
        action="store_true",
        help="after building verify bench against commit history",
    )
    parser.add_argument(
        "--local-emsdk",
        action="store_true",
        help="force using local emsdk, even if it does not match the pinned version",
    )
    parser.add_argument(
        "targets",
        nargs="*",
        choices=[
            "clean",
            *{tag for info in targets.values() for tag in info.tags},
            *targets.keys(),
        ],
        default=[default_target],
    )

    args = parser.parse_args()

    if "clean" in args.targets:
        clean()

    selected_targets = [
        name
        for name, target in targets.items()
        if name in args.targets or any(tag in args.targets for tag in target.tags)
    ]

    if selected_targets:
        print(f"selected targets: {', '.join(selected_targets)}")
        print(f"cxx flags: {args.cxx_flags}")
        print(f"ld flags: {args.ld_flags}")

    for name in selected_targets:
        print()
        print(f"# {name}")
        command = get_command(name, args.local_emsdk, "em++")
        build_target(
            name,
            local_emsdk=args.local_emsdk,
            cxx_flags=args.cxx_flags,
            ld_flags=args.ld_flags,
            pgo=args.pgo,
            command=command,
        )
        if args.verify_bench:
            verify_bench(name)


def build_target(
    name: TargetName,
    *,
    local_emsdk: bool,
    cxx_flags: str,
    ld_flags: str,
    pgo: bool,
    command: list[str],
) -> None:
    fetch_sources(name)

    target_dir = fishes_dir / name

    sources = [
        f
        for f in glob.glob("**/*.cpp", root_dir=target_dir / "src", recursive=True)
        if f not in ignore_sources
    ]

    if pgo:
        cxx_flags = f"{cxx_flags} -fprofile-instr-use={collect_pgo_profile(name, sources, local_emsdk=local_emsdk, cxx_flags=cxx_flags, ld_flags=ld_flags, command=command)}"

    run_make(name, sources, cxx_flags=cxx_flags, ld_flags=ld_flags, command=command)


def collect_pgo_profile(
    name: TargetName,
    sources: list[str],
    *,
    local_emsdk: bool,
    cxx_flags: str,
    ld_flags: str,
    command: list[str],
) -> Path:
    target_dir = fishes_dir / name
    profile_raw = target_dir / "pgo.profraw"
    profile_data = target_dir / "pgo.profdata"
    profile_raw.unlink(missing_ok=True)

    run_make(
        name,
        sources,
        cxx_flags=f"{cxx_flags} -fprofile-instr-generate={profile_raw} --closure=0",
        ld_flags=f"{ld_flags} -sNODERAWFS",
        command=command,
    )

    print(f"running instrumented bench to collect pgo profile for {name}")
    if bench_run(name) is None:
        print(f"instrumented bench run failed for {name}")
        sys.exit(1)
    if not profile_raw.exists() or profile_raw.stat().st_size == 0:
        print(f"instrumented bench run failed to write {profile_raw}")
        sys.exit(1)

    llvm_root = Path(
        subprocess.check_output(
            get_command(name, local_emsdk, "em-config", "LLVM_ROOT"), text=True
        ).strip()
    )
    llvm_profdata = llvm_root / "llvm-profdata"
    subprocess.check_call(
        get_command(
            name,
            local_emsdk,
            str(llvm_profdata),
            "merge",
            f"-output={profile_data}",
            str(profile_raw),
        )
    )
    return profile_data


def run_make(
    name: TargetName,
    sources: list[str],
    *,
    cxx_flags: str,
    ld_flags: str,
    command: list[str],
) -> None:
    target_dir = fishes_dir / name
    makefile_path = target_dir / "Makefile.tmp"

    contents = makefile(name, sources, cxx_flags, ld_flags)
    if not makefile_path.exists() or makefile_path.read_text() != contents:
        makefile_path.write_text(contents)

    make_command = ["make", "-f", "Makefile.tmp", "-j"]
    make_command.append(f"CXX={shlex.join(command)}")
    subprocess.check_call(make_command, cwd=target_dir)

    for asset in [f"{name}.js", f"{name}.wasm"]:
        (target_dir / asset).replace(script_dir / asset)


def verify_bench(name: TargetName) -> None:
    reference = bench_reference(name)
    if reference is None:
        print(f"no bench reference found in commit history for {name}")
        sys.exit(1)
    print(f"reference bench: {reference}")

    signature = bench_run(name)
    if signature is None:
        print(f"no bench signature obtained for {name} (crash or timeout?)")
        sys.exit(1)
    if signature != reference:
        print(
            f"bench signature mismatch for {name}: reference {reference}, obtained {signature}"
        )
        sys.exit(1)
    print(f"bench signature ok for {name}: {signature}")


def bench_reference(name: TargetName) -> str | None:
    bench_re = re.compile(r"^[ \t]*[Bb]ench[ :]+([0-9]+)[ \t]*$", re.MULTILINE)

    body = subprocess.check_output(
        [
            "git",
            "log",
            "--max-count=1",
            "--format=%B",
            "--extended-regexp",
            "--grep",
            r"^[[:space:]]*[Bb]ench[ :]+[0-9]+[[:space:]]*$",
            "HEAD",
        ],
        cwd=fishes_dir / name,
        text=True,
    )
    matches = bench_re.findall(body)
    return matches[-1] if matches else None


def bench_run(name: TargetName) -> str | None:
    signature_re = re.compile(r"Nodes searched\s*:\s*([0-9]+)")

    proc = subprocess.Popen(
        ["node", str(script_dir / "tools" / "wasm-cli.ts"), f"{name}.js"],
        cwd=script_dir,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert proc.stdin is not None and proc.stdout is not None

    watchdog = threading.Timer(300, proc.kill)
    watchdog.start()

    signature = None
    try:
        proc.stdin.write("bench\n")
        proc.stdin.close()
        for line in proc.stdout:
            sys.stdout.write(line)
            match = signature_re.search(line)
            if match:
                signature = match.group(1)
        if proc.wait() != 0:
            signature = None  # Fail on unclean exit
    finally:
        watchdog.cancel()
        proc.kill()
        proc.wait()
    return signature


def fetch_sources(name: TargetName) -> None:
    target = targets[name]
    checkout_dir = fishes_dir / name

    env = os.environ | {
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "advice.detachedHead",
        "GIT_CONFIG_VALUE_0": "false",
    }

    try:
        checkout_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        print(f"skipping clone and patch for {name} (already exists)")
        subprocess.check_call(
            ["git", "tag", "-f", "stockfish-web/base", target.commit],
            env=env,
            cwd=checkout_dir,
        )
    else:
        subprocess.check_call(
            ["git", "clone", target.repo, name], env=env, cwd=fishes_dir
        )
        subprocess.check_call(
            ["git", "checkout", target.commit], env=env, cwd=checkout_dir
        )
        subprocess.check_call(
            ["git", "tag", "-f", "stockfish-web/base", target.commit],
            env=env,
            cwd=checkout_dir,
        )
        for patch in target.patches:
            subprocess.check_call(
                ["git", "am", patches_dir / patch], env=env, cwd=checkout_dir
            )


def clean() -> None:
    clean_list = [
        *fishes_dir.glob("**/*.o"),
        *fishes_dir.glob("*/Makefile.tmp"),
        *fishes_dir.glob("*/pgo.profraw"),
        *fishes_dir.glob("*/pgo.profdata"),
        *[
            script_dir / f"{name}.{ext}"
            for name in targets
            for ext in ["js", "worker.js", "wasm", "js.map", "worker.js.map"]
        ],
    ]

    for path in clean_list:
        path.unlink(missing_ok=True)


@functools.cache
def which_local_emsdk_version() -> tuple[int, int, int] | None:
    try:
        stdout = subprocess.check_output(["emcc", "--version"], text=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    version_match = re.search(r"([\d]+)\.([\d]+)\.([\d]+)", stdout)
    if version_match is None:
        return None
    major, minor, patch = map(int, version_match.groups())
    return major, minor, patch


@functools.cache
def which_runtime() -> str | None:
    return shutil.which("podman") or shutil.which("docker")


def get_command(name: TargetName, local_emsdk: bool, *args: str) -> list[str]:
    target = targets[name]
    local_emsdk_version = which_local_emsdk_version()
    if local_emsdk or local_emsdk_version == target.emcc:
        return [*args]

    runtime = which_runtime()
    if runtime is None:
        print(
            f"either emsdk {join_version(target.emcc)} (or any with --local-emsdk), podman, or docker is needed to build {name}"
        )
        sys.exit(1)

    cache = emsdk_cache_dir / join_version(target.emcc)
    cache.mkdir(parents=True, exist_ok=True)

    image = f"docker.io/emscripten/emsdk:{join_version(target.emcc)}"
    command = [runtime, "run", "--rm"]
    if Path(runtime).name == "docker":
        command += ["-u", f"{os.getuid()}:{os.getgid()}"]
    command += [
        "-v",
        f"{cache}:/emsdk/upstream/emscripten/cache",
        "-v",
        f"{script_dir}:{script_dir}",
        "-w",
        str(fishes_dir / name),
        image,
        *args,
    ]
    return command


if __name__ == "__main__":
    main()
