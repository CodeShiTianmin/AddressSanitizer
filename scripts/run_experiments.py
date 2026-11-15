#!/usr/bin/env python3
"""Run the experiment matrix defined in config/experiments.json.

For every repetition, every benchmark is run once in every variant (the variant
order is rotated per repetition so that slow drifts do not bias one variant).
Each run is pinned to one CPU. One JSON object per run is appended to
results/raw/<experiment>/runs.jsonl; nothing is aggregated here.

usage: scripts/run_experiments.py <experiment> [--runs N] [--bench a,b] [--cpu C]
       scripts/run_experiments.py malloc-profile | binsize
"""
import argparse, json, os, platform, shutil, subprocess, sys, tempfile, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config" / "experiments.json").read_text())
HARNESS_BUILD = ROOT / "build" / "harness"


def build_helpers():
    HARNESS_BUILD.mkdir(parents=True, exist_ok=True)
    for name in ("procstat", "malloccount"):
        so = HARNESS_BUILD / f"lib{name}.so"
        src = ROOT / "harness" / f"{name}.c"
        if not so.exists() or so.stat().st_mtime < src.stat().st_mtime:
            subprocess.run([os.environ.get("CC", "clang"), "-O2", "-shared", "-fPIC", str(src), "-o", str(so)], check=True)


def resolve_options(spec: str) -> str:
    parts = []
    for tok in spec.split(":") if spec else []:
        parts.append(CFG["asan_options"].get(tok, tok))
    return ":".join(parts)


def parse_procstat(d: Path, bin_dir: Path):
    procs = []
    for f in sorted(d.iterdir()):
        rec = {}
        for line in f.read_text().splitlines():
            k, _, v = line.partition(":")
            v = v.strip()
            rec[k] = v if k == "Exe" else int(v.split()[0])
        if str(rec.get("Exe", "")).startswith(str(bin_dir)):
            procs.append(rec)
    return procs


def cpu_steal(cpu):
    """Cumulative steal time (s) of one CPU: time the hypervisor ran something else."""
    with open("/proc/stat") as f:
        for line in f:
            if line.startswith(f"cpu{cpu} "):
                return int(line.split()[8]) / os.sysconf("SC_CLK_TCK")
    return 0.0


def run_once(bench, build, asan_options, cpu, scratch, preload, extra_env=None):
    bin_dir = ROOT / "build" / build / bench / "bin"
    out = Path(tempfile.mkdtemp(dir=scratch))
    pdir = out / "_procstat"; pdir.mkdir()
    env = dict(os.environ, BIN=str(bin_dir), DATA=str(ROOT / "data"), OUT=str(out),
               BENCH_DIR=str(ROOT / "benchmarks" / bench), PROCSTAT_DIR=str(pdir),
               LD_PRELOAD=str(preload), ASAN_OPTIONS=asan_options)
    env.update(extra_env or {})
    cmd = ["taskset", "-c", str(cpu), "bash", "-e", str(ROOT / "benchmarks" / bench / "run.sh")]
    log = out / "_run.log"
    with log.open("wb") as lf:
        st0 = cpu_steal(cpu)
        t0 = time.perf_counter()
        p = subprocess.Popen(cmd, env=env, stdout=lf, stderr=subprocess.STDOUT)
        _, wstatus, ru = os.wait4(p.pid, 0)
        wall = time.perf_counter() - t0
        steal = cpu_steal(cpu) - st0
    status = os.waitstatus_to_exitcode(wstatus)
    p.returncode = status
    rec = dict(bench=bench, build=build, asan_options=asan_options, wall_s=round(wall, 4), steal_s=round(steal, 2),
               user_s=round(ru.ru_utime, 4), sys_s=round(ru.ru_stime, 4), maxrss_kb=ru.ru_maxrss,
               rc=status, procs=parse_procstat(pdir, bin_dir),
               log_tail=log.read_text(errors="replace")[-3000:] if status else "")
    shutil.rmtree(out, ignore_errors=True)
    return rec


def benchmarks(sel):
    allb = sorted(p.name for p in (ROOT / "benchmarks").iterdir() if (p / "run.sh").exists())
    return [b for b in allb if not sel or b in sel.split(",")]


def malloc_profile(args):
    """Count heap allocations of every benchmark once (base build)."""
    outdir = ROOT / "results" / "raw" / "malloc-profile"; outdir.mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix="asanrepl-"))
    with (outdir / "profile.jsonl").open("w") as fo:
        for b in benchmarks(args.bench):
            mdir = scratch / f"m-{b}"; mdir.mkdir()
            rec = run_once(b, "base", "", args.cpu, scratch, HARNESS_BUILD / "libmalloccount.so",
                           {"MALLOCCOUNT_DIR": str(mdir)})
            bin_dir = str(ROOT / "build" / "base" / b / "bin")
            tot = {}
            for f in mdir.iterdir():
                kv = dict(l.split(" ", 1) for l in f.read_text().splitlines())
                if kv["exe"].startswith(bin_dir):
                    for k, v in kv.items():
                        if k != "exe": tot[k] = tot.get(k, 0) + int(v)
            rec.update(experiment="malloc-profile", variant="base", malloc=tot)
            print(f"[malloc] {b:10s} allocs={tot.get('allocs',0):>12,d} bytes={tot.get('bytes',0):>15,d} rc={rec['rc']}")
            fo.write(json.dumps(rec) + "\n")
    shutil.rmtree(scratch, ignore_errors=True)


def binsize(args):
    """Record executable sizes (file size and text/data/bss) of every build."""
    outdir = ROOT / "results" / "raw" / "binsize"; outdir.mkdir(parents=True, exist_ok=True)
    size_tool = shutil.which("llvm-size-18") or shutil.which("llvm-size") or "size"
    with (outdir / "binsize.jsonl").open("w") as fo:
        for cfg in sorted(p.name for p in (ROOT / "build").iterdir() if p.name != "harness"):
            for b in benchmarks(args.bench):
                bdir = ROOT / "build" / cfg / b / "bin"
                for f in sorted(bdir.glob("*")) if bdir.is_dir() else []:
                    if not os.access(f, os.X_OK):
                        continue
                    out = subprocess.run([size_tool, str(f)], capture_output=True, text=True).stdout.split("\n")[1].split()
                    rec = dict(build=cfg, bench=b, exe=f.name, file_bytes=f.stat().st_size,
                               text=int(out[0]), data=int(out[1]), bss=int(out[2]))
                    fo.write(json.dumps(rec) + "\n")
        # constant contribution of the statically linked ASan run-time: an empty program
        tmp = Path(tempfile.mkdtemp())
        (tmp / "empty.c").write_text("int main(void) { return 0; }\n")
        for cfg, flags in (("base", []), ("asan", ["-fsanitize=address"])):
            exe = tmp / f"empty-{cfg}"
            subprocess.run([os.environ.get("CC", "clang"), "-O2", *flags, str(tmp / "empty.c"), "-o", str(exe)], check=True)
            out = subprocess.run([size_tool, str(exe)], capture_output=True, text=True).stdout.split("\n")[1].split()
            fo.write(json.dumps(dict(build=cfg, bench="_empty", exe="empty", file_bytes=exe.stat().st_size,
                                     text=int(out[0]), data=int(out[1]), bss=int(out[2]))) + "\n")
        # NNUE networks embedded in stockfish's .text (identical in every build)
        nnue = sum(f.stat().st_size for f in (ROOT / "downloads").glob("nn-*.nnue"))
        fo.write(json.dumps(dict(build="any", bench="stockfish", exe="_embedded_nnue", file_bytes=nnue, text=nnue, data=0, bss=0)) + "\n")
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"[binsize] written to {outdir}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("experiment")
    ap.add_argument("--runs", type=int)
    ap.add_argument("--bench", default="")
    ap.add_argument("--cpu", type=int, default=int(os.environ.get("BENCH_CPU", os.cpu_count() - 1)))
    ap.add_argument("--tag", default="", help="suffix for the output directory")
    args = ap.parse_args()
    build_helpers()
    if args.experiment == "malloc-profile":
        return malloc_profile(args)
    if args.experiment == "binsize":
        return binsize(args)
    exp = CFG["experiments"][args.experiment]
    runs = args.runs or exp["runs"]
    variants = exp["variants"]
    benches = benchmarks(args.bench)
    outdir = ROOT / "results" / "raw" / (args.experiment + (f"-{args.tag}" if args.tag else ""))
    outdir.mkdir(parents=True, exist_ok=True)
    for v in variants:
        for b in benches:
            if not (ROOT / "build" / v["build"] / b / "bin").is_dir():
                sys.exit(f"missing build/{v['build']}/{b} - run 'make build' first")
    scratch = Path(os.environ.get("SCRATCH", ROOT / "scratch")); scratch.mkdir(exist_ok=True)
    meta = dict(experiment=args.experiment, runs=runs, cpu=args.cpu, benches=benches, variants=variants,
                host=platform.node(), kernel=platform.release(),
                started=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    (outdir / f"meta-{int(time.time())}.json").write_text(json.dumps(meta, indent=1))
    preload = HARNESS_BUILD / "libprocstat.so"
    runs_file = outdir / "runs.jsonl"
    rep0 = max((json.loads(l)["rep"] for l in runs_file.read_text().splitlines()), default=0) if runs_file.exists() else 0
    print(f"[run] {args.experiment}: {len(benches)} benchmarks x {len(variants)} variants x {runs} runs on CPU {args.cpu}")
    for b in benches:  # warm-up (file cache, page cache for inputs); not recorded
        run_once(b, "base", "", args.cpu, scratch, preload)
    with runs_file.open("a") as fo:
        for rep in range(rep0 + 1, rep0 + runs + 1):
            for b in benches:
                k = (rep - 1) % len(variants)
                for v in variants[k:] + variants[:k]:
                    rec = run_once(b, v["build"], resolve_options(v["asan_options"]), args.cpu, scratch, preload)
                    rec.update(experiment=args.experiment, variant=v["name"], rep=rep,
                               time=datetime.now(timezone.utc).isoformat(timespec="seconds"))
                    fo.write(json.dumps(rec) + "\n"); fo.flush()
                    peak = max((p.get("VmHWM", 0) for p in rec["procs"]), default=0)
                    print(f"[run] rep{rep} {b:10s} {v['name']:13s} wall={rec['wall_s']:8.3f}s hwm={peak/1024:8.1f}MB rc={rec['rc']}", flush=True)
                    if rec["rc"] != 0:
                        print(rec["log_tail"], file=sys.stderr)


if __name__ == "__main__":
    main()
