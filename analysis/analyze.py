#!/usr/bin/env python3
"""Aggregate results/raw/*/runs.jsonl into summary CSVs, LaTeX tables/macros and figures.

Every number in the report comes from here:
  results/summary/*.csv        machine-readable aggregates
  report/generated/*.tex       LaTeX tables and \\newcommand macros used by report.tex
  report/figures/*.pdf         figures
Slowdowns are computed per repetition (variant run / base run of the same
repetition, same benchmark) and reported as mean +- sample standard deviation
over repetitions. Averages over benchmarks are arithmetic means (the paper's
"average" bar equals the arithmetic mean of its per-benchmark bars).
"""
import json, sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paper_data as P  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW, SUM = ROOT / "results" / "raw", ROOT / "results" / "summary"
GEN, FIG = ROOT / "report" / "generated", ROOT / "report" / "figures"
for d in (SUM, GEN, FIG):
    d.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.size": 8, "figure.dpi": 150, "savefig.bbox": "tight"})
ORDER = ["perl", "bzip2", "gnugo", "hmmer", "stockfish", "x264", "libxml2", "tramp3d", "lulesh", "lua", "sqlite"]
MACROS = {}


def macro(name, value):
    MACROS[name] = value


def mname(b):
    """benchmark name -> letters-only LaTeX macro suffix (bzip2 -> Bzip)"""
    return "".join(c for c in b if c.isalpha()).capitalize()


def load(exp):
    f = RAW / exp / "runs.jsonl"
    if not f.exists():
        return None
    rows = []
    for line in f.read_text().splitlines():
        r = json.loads(line)
        procs = r["procs"]
        rows.append(dict(bench=r["bench"], variant=r["variant"], rep=r["rep"], wall=r["wall_s"], rc=r["rc"],
                         user=r["user_s"], sys=r["sys_s"], maxrss=r["maxrss_kb"] / 1024,
                         vmpeak=max((p.get("VmPeak", 0) for p in procs), default=np.nan) / 1024,
                         vmhwm=max((p.get("VmHWM", 0) for p in procs), default=np.nan) / 1024,
                         vmstk=max((p.get("VmStk", 0) for p in procs), default=np.nan),
                         steal=r.get("steal_s", np.nan)))
    df = pd.DataFrame(rows)
    bad = df[df.rc != 0]
    if len(bad):
        print(f"[analyze] WARNING {exp}: {len(bad)} failed runs excluded:\n{bad[['bench','variant','rep','rc']]}")
    df = df[df.rc == 0]
    nvar = df.variant.nunique()
    full = df.groupby(["bench", "rep"]).variant.transform("nunique") == nvar
    if (~full).any():
        print(f"[analyze] NOTE {exp}: {(~full).sum()} runs from incomplete (bench, rep) groups ignored")
    return df[full]


def ratios(df, variant, metric="wall"):
    """Per-repetition ratio variant/base for every benchmark -> DataFrame[bench, rep, ratio]."""
    base = df[df.variant == "base"].set_index(["bench", "rep"])[metric]
    v = df[df.variant == variant].set_index(["bench", "rep"])[metric]
    r = (v / base).dropna().rename("ratio").reset_index()
    return r


def summarize(r):
    """per-benchmark mean/sd + benchmark-average mean/sd (sd over repetitions of the per-rep average)."""
    per = r.groupby("bench").ratio.agg(["mean", "std", "count"])
    per = per.reindex([b for b in ORDER if b in per.index])
    avg_rep = r.groupby("rep").ratio.mean()
    gavg_rep = r.groupby("rep").ratio.apply(lambda x: float(np.exp(np.log(x).mean())))
    return per, (avg_rep.mean(), avg_rep.std()), (gavg_rep.mean(), gavg_rep.std())


def pm(m, s, d=2):
    return f"{m:.{d}f}$\\pm${s:.{d}f}"


def tex_table(path, header, rows, colspec, caption=None):
    lines = [f"\\begin{{tabular}}{{{colspec}}}", "\\toprule", " & ".join(header) + " \\\\", "\\midrule"]
    for r in rows:
        lines.append("\\midrule" if r == "MIDRULE" else " & ".join(str(c) for c in r) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (GEN / path).write_text("\n".join(lines) + "\n")


# ---------------------------------------------------------------- main experiment
def main_experiment():
    df = load("main")
    if df is None:
        print("[analyze] no main results"); return
    nrep = df.rep.nunique()
    macro("MainRuns", nrep)
    wall = df.groupby(["bench", "variant"]).wall.agg(["mean", "std"]).unstack()
    wall.to_csv(SUM / "main_walltime.csv")
    rw, wo = ratios(df, "asan"), ratios(df, "asanwo")
    per_rw, avg_rw, gavg_rw = summarize(rw)
    per_wo, avg_wo, gavg_wo = summarize(wo)
    out = pd.DataFrame({"rw_mean": per_rw["mean"], "rw_sd": per_rw["std"], "wo_mean": per_wo["mean"], "wo_sd": per_wo["std"]})
    out.to_csv(SUM / "main_slowdown.csv")
    for b in out.index:
        macro(f"RW{mname(b)}", f"{out['rw_mean'][b]:.2f}"); macro(f"WO{mname(b)}", f"{out['wo_mean'][b]:.2f}")
        macro(f"RWsd{mname(b)}", f"{out['rw_sd'][b]:.2f}")
    cv = (wall["std"]["base"] / wall["mean"]["base"])
    macro("MedBaseCV", f"{cv.median()*100:.0f}")
    # robustness: slowdown of medians, and of (wall - hypervisor steal) where steal was recorded
    med = df.groupby(["bench", "variant"]).wall.median().unstack()
    macro("MedianAvgRW", f"{(med['asan']/med['base']).mean():.2f}"); macro("MedianAvgWO", f"{(med['asanwo']/med['base']).mean():.2f}")
    if "steal" in df and df.steal.notna().any():
        ds = df[df.steal.notna()].copy()
        ds["cpu"] = ds.wall - ds.steal
        macro("StealRuns", ds.rep.nunique())
        macro("StealPct", f"{(ds.steal.sum()/ds.wall.sum())*100:.0f}")
        macro("StealMaxPct", f"{(ds.steal/ds.wall).max()*100:.0f}")
        cs = summarize(ratios(ds, "asan", "cpu")); csw = summarize(ratios(ds, "asanwo", "cpu"))
        ws = summarize(ratios(ds, "asan", "wall"))
        macro("StealAdjRW", f"{cs[1][0]:.2f}"); macro("StealAdjRWsd", f"{cs[1][1]:.2f}")
        macro("StealAdjWO", f"{csw[1][0]:.2f}"); macro("StealRawRW", f"{ws[1][0]:.2f}")
        macro("StealAdjMeanSD", f"{cs[0]['std'].mean():.2f}"); macro("StealRawMeanSD", f"{ws[0]['std'].mean():.2f}")
        cvb = ds[ds.variant == "base"].groupby("bench")
        macro("StealCVraw", f"{(cvb.wall.std()/cvb.wall.mean()).median()*100:.0f}")
        macro("StealCVadj", f"{(cvb.cpu.std()/cvb.cpu.mean()).median()*100:.0f}")
    macro("OurAvgRW", f"{avg_rw[0]:.2f}"); macro("OurAvgRWsd", f"{avg_rw[1]:.2f}")
    macro("OurAvgWO", f"{avg_wo[0]:.2f}"); macro("OurAvgWOsd", f"{avg_wo[1]:.2f}")
    macro("OurGeoRW", f"{gavg_rw[0]:.2f}"); macro("OurGeoWO", f"{gavg_wo[0]:.2f}")
    macro("OurAvgRWpct", f"{(avg_rw[0]-1)*100:.0f}"); macro("OurAvgWOpct", f"{(avg_wo[0]-1)*100:.0f}")
    mapped = [b for b in per_rw.index if b in P.STRICT]
    m_rw = rw[rw.bench.isin(mapped)].groupby("rep").ratio.mean()
    m_wo = wo[wo.bench.isin(mapped)].groupby("rep").ratio.mean()
    p_rw = np.mean([P.FIG2_RW[P.COUNTERPART[b]] for b in mapped])
    p_wo = np.mean([P.FIG2_WO[P.COUNTERPART[b]] for b in mapped])
    macro("OurMapRW", f"{m_rw.mean():.2f}"); macro("OurMapRWsd", f"{m_rw.std():.2f}")
    macro("OurMapWO", f"{m_wo.mean():.2f}"); macro("OurMapWOsd", f"{m_wo.std():.2f}")
    macro("PaperMapRW", f"{p_rw:.2f}"); macro("PaperMapWO", f"{p_wo:.2f}")
    # overhead share removed by not instrumenting reads
    macro("WOShare", f"{(avg_wo[0]-1)/(avg_rw[0]-1)*100:.0f}")
    macro("PaperWOShare", f"{(P.PAPER_AVG_WO-1)/(P.PAPER_AVG_RW-1)*100:.0f}")
    def gap(name, ours, paper):
        macro(f"Gap{name}", f"{ours-paper:+.2f}"); macro(f"Gap{name}Rel", f"{(ours-paper)/paper*100:+.0f}\\%")
    gap("RWAll", avg_rw[0], P.PAPER_AVG_RW); gap("WOAll", avg_wo[0], P.PAPER_AVG_WO)
    gap("RWMap", m_rw.mean(), p_rw); gap("WOMap", m_wo.mean(), p_wo)
    gap("Perl", per_rw["mean"]["perl"], P.FIG2_RW["400.perlbench"]); gap("Xml", per_rw["mean"]["libxml2"], P.FIG2_RW["483.xalancbmk"])
    top = per_rw["mean"].sort_values(ascending=False)
    macro("TopOneName", top.index[0]); macro("TopOne", f"{top.iloc[0]:.2f}")
    macro("TopTwoName", top.index[1]); macro("TopTwo", f"{top.iloc[1]:.2f}")
    macro("MinName", top.index[-1]); macro("MinVal", f"{top.iloc[-1]:.2f}")
    macro("MaxRWsd", f"{per_rw['std'].max():.2f}")
    macro("MaxBaseCV", f"{(wall['std']['base']/wall['mean']['base']).max()*100:.1f}")

    # Table: Paper vs Ours, run time
    rows = []
    for b in per_rw.index:
        cp = P.COUNTERPART.get(b)
        rows.append([f"\\texttt{{{b}}}", cp or "--", f"{wall['mean']['base'][b]:.2f}",
                     f"{P.FIG2_RW[cp]:.2f}" if cp else "--", pm(per_rw['mean'][b], per_rw['std'][b]),
                     f"{P.FIG2_WO[cp]:.2f}" if cp else "--", pm(per_wo['mean'][b], per_wo['std'][b])])
    rows.append("MIDRULE")
    rows.append(["Average (7 counterparts)", "", "", f"{p_rw:.2f}", pm(m_rw.mean(), m_rw.std()), f"{p_wo:.2f}", pm(m_wo.mean(), m_wo.std())])
    rows.append(["Average (all 11)", "SPEC avg.", "", f"{P.PAPER_AVG_RW:.2f}", pm(*avg_rw), f"{P.PAPER_AVG_WO:.2f}", pm(*avg_wo)])
    rows.append(["Geometric mean (all 11)", "", "", "1.70", pm(*gavg_rw), "1.25", pm(*gavg_wo)])
    tex_table("tab_time.tex", ["Ours", "SPEC counterpart", "Base [s]", "Paper R+W", "Ours R+W", "Paper W", "Ours W"],
              rows, "llrrrrr")

    # Figure: slowdown per benchmark (like Figure 2) with paper markers
    benches = list(per_rw.index) + ["average"]
    x = np.arange(len(benches)); w = 0.38
    rwm = list(per_rw["mean"]) + [avg_rw[0]]; rws = list(per_rw["std"]) + [avg_rw[1]]
    wom = list(per_wo["mean"]) + [avg_wo[0]]; wos = list(per_wo["std"]) + [avg_wo[1]]
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    ax.bar(x - w / 2, wom, w, yerr=wos, capsize=2, color="0.45", label="Ours: writes only")
    ax.bar(x + w / 2, rwm, w, yerr=rws, capsize=2, color="white", edgecolor="black", hatch="///", label="Ours: reads and writes")
    prw = [P.FIG2_RW.get(P.COUNTERPART.get(b)) for b in per_rw.index] + [P.PAPER_AVG_RW]
    pwo = [P.FIG2_WO.get(P.COUNTERPART.get(b)) for b in per_rw.index] + [P.PAPER_AVG_WO]
    ax.scatter([xi + w / 2 for xi, v in zip(x, prw) if v], [v for v in prw if v], marker="D", color="tab:red", zorder=3, s=14, label="Paper (counterpart): reads and writes")
    ax.scatter([xi - w / 2 for xi, v in zip(x, pwo) if v], [v for v in pwo if v], marker="v", color="tab:blue", zorder=3, s=14, label="Paper (counterpart): writes only")
    ax.set_xticks(x); ax.set_xticklabels(benches, rotation=35, ha="right")
    ax.set_ylim(1.0, max(rwm + [v for v in prw if v]) * 1.08); ax.set_ylabel("slowdown vs. clang -O2")
    ax.axhline(1, color="black", lw=0.5); ax.grid(axis="y", lw=0.3)
    ax.legend(ncol=2, fontsize=6.5, loc="upper right")
    fig.savefig(FIG / "fig_slowdown.pdf"); plt.close(fig)

    # Memory (C3) -- VmHWM (peak RSS) and VmPeak (paper's metric) and stack
    mem = df.groupby(["bench", "variant"])[["vmhwm", "vmpeak", "vmstk", "maxrss"]].mean().unstack()
    mem.to_csv(SUM / "main_memory.csv")
    hw = ratios(df, "asan", "vmhwm")
    per_hw, avg_hw, _ = summarize(hw)
    tot_base = mem["vmhwm"]["base"].sum(); tot_asan = mem["vmhwm"]["asan"].sum()
    for b in per_hw.index:
        macro(f"Mem{mname(b)}", f"{per_hw['mean'][b]:.2f}")
        macro(f"MemAdd{mname(b)}", f"{mem['vmhwm']['asan'][b]-mem['vmhwm']['base'][b]:.0f}")
    macro("GapMem", f"{tot_asan/tot_base-P.PAPER_MEM_TOTAL:+.2f}"); macro("GapMemRel", f"{(tot_asan/tot_base-P.PAPER_MEM_TOTAL)/P.PAPER_MEM_TOTAL*100:+.0f}\\%")
    macro("OurMemTotal", f"{tot_asan/tot_base:.2f}"); macro("OurMemAvg", f"{avg_hw[0]:.2f}")
    macro("OurMemAvgsd", f"{avg_hw[1]:.2f}")
    macro("VmPeakAsanTB", f"{mem['vmpeak']['asan'].min()/1024/1024:.1f}")
    macro("VmPeakAsanTBmax", f"{mem['vmpeak']['asan'].max()/1024/1024:.1f}")
    pmem = {b: P.TABLE1[P.COUNTERPART[b]][1] / P.TABLE1[P.COUNTERPART[b]][0] for b in per_hw.index if P.COUNTERPART.get(b)}
    mapped_m = [b for b in per_hw.index if b in P.STRICT]
    pt = sum(P.TABLE1[P.COUNTERPART[b]][1] for b in mapped_m) / sum(P.TABLE1[P.COUNTERPART[b]][0] for b in mapped_m)
    ot = mem["vmhwm"]["asan"][mapped_m].sum() / mem["vmhwm"]["base"][mapped_m].sum()
    macro("PaperMemMapTotal", f"{pt:.2f}"); macro("OurMemMapTotal", f"{ot:.2f}")
    wo_hw = ratios(df, "asanwo", "vmhwm"); macro("OurMemWOTotal", f"{mem['vmhwm']['asanwo'].sum()/tot_base:.2f}")
    rows = []
    for b in per_hw.index:
        cp = P.COUNTERPART.get(b)
        rows.append([f"\\texttt{{{b}}}", f"{mem['vmhwm']['base'][b]:.0f}", f"{mem['vmhwm']['asan'][b]:.0f}",
                     pm(per_hw['mean'][b], per_hw['std'][b]), f"{pmem[b]:.2f}" if cp else "--",
                     f"{mem['vmpeak']['base'][b]:.0f}", f"{mem['vmpeak']['asan'][b]/1024/1024:.1f} TB"])
    rows.append("MIDRULE")
    rows.append(["Total (7 counterparts)", f"{mem['vmhwm']['base'][mapped_m].sum():.0f}", f"{mem['vmhwm']['asan'][mapped_m].sum():.0f}", f"{ot:.2f}", f"{pt:.2f}", "", ""])
    rows.append(["Total (all 11)", f"{tot_base:.0f}", f"{tot_asan:.0f}", f"{tot_asan/tot_base:.2f}", f"{P.PAPER_MEM_TOTAL:.2f}", "", ""])
    rows.append(["Mean of ratios", "", "", pm(*avg_hw), "", "", ""])
    tex_table("tab_memory.tex", ["Benchmark", "Base RSS", "ASan RSS", "Ours incr.", "Paper incr.", "Base VmPeak", "ASan VmPeak"],
              rows, "lrrrrrr")
    # stack
    rows = []
    for b in [b for b in ORDER if b in mem.index]:
        sb, sa = mem["vmstk"]["base"][b], mem["vmstk"]["asan"][b]
        cp = P.COUNTERPART.get(b)
        ps = f"{P.TABLE2[cp][1]/P.TABLE2[cp][0]:.2f}x" if cp in P.TABLE2 else "--"
        rows.append([f"\\texttt{{{b}}}", f"{sb:.0f}", f"{sa:.0f}", f"{sa/sb:.2f}x", ps])
    tex_table("tab_stack.tex", ["Benchmark", "Base VmStk [KB]", "ASan VmStk [KB]", "Increase", "Paper (counterpart)"], rows, "lrrrr")
    stk = mem["vmstk"]["asan"] / mem["vmstk"]["base"]
    macro("StackNoticeable", int((stk > 1.05).sum())); macro("StackOverTen", int((stk > 1.10).sum()))

    fig, ax = plt.subplots(figsize=(7.2, 2.4))
    x = np.arange(len(per_hw.index)); w = 0.38
    ax.bar(x - w / 2, per_hw["mean"], w, yerr=per_hw["std"], capsize=2, color="0.6", label="Ours (VmHWM, peak RSS)")
    ax.bar(x + w / 2, [pmem.get(b, np.nan) for b in per_hw.index], w, color="tab:red", alpha=0.7, label="Paper Table 1 (counterpart, VmPeak)")
    ax.set_xticks(x); ax.set_xticklabels(per_hw.index, rotation=35, ha="right")
    ax.set_ylabel("memory increase (x)"); ax.set_yscale("log"); ax.grid(axis="y", lw=0.3)
    ax.axhline(1, color="black", lw=0.5); ax.legend(fontsize=6.5)
    fig.savefig(FIG / "fig_memory.pdf"); plt.close(fig)
    return per_rw


# ---------------------------------------------------------------- controls
def controls():
    df = load("controls")
    if df is None:
        return
    macro("CtrlRuns", df.rep.nunique())
    res = {}
    for v in ("asan", "asan-default", "asanlean"):
        res[v] = summarize(ratios(df, v))
    memd = df.groupby(["bench", "variant"]).vmhwm.mean().unstack()
    memd.to_csv(SUM / "controls_memory.csv")
    pd.DataFrame({v: res[v][0]["mean"] for v in res}).to_csv(SUM / "controls_slowdown.csv")
    rows = []
    common = [b for b in res["asan"][0].index if all(b in res[v][0].index for v in res)]
    for b in common:
        rows.append([f"\\texttt{{{b}}}"] + [pm(res[v][0]['mean'][b], res[v][0]['std'][b]) for v in res] +
                    [f"{memd['asan'][b]/memd['base'][b]:.2f}", f"{memd['asan-default'][b]/memd['base'][b]:.2f}"])
    rows.append("MIDRULE")
    rows.append(["Average"] + [pm(*res[v][1]) for v in res] +
                [f"{memd['asan'].sum()/memd['base'].sum():.2f}", f"{memd['asan-default'].sum()/memd['base'].sum():.2f}"])
    tex_table("tab_controls.tex", ["Benchmark", "paper opts", "default opts", "lean build", "mem paper", "mem default"], rows, "lrrrrr")
    macro("CtrlAsan", f"{res['asan'][1][0]:.2f}"); macro("CtrlDefault", f"{res['asan-default'][1][0]:.2f}")
    macro("CtrlLean", f"{res['asanlean'][1][0]:.2f}")
    macro("CtrlMemDefault", f"{memd['asan-default'].sum()/memd['base'].sum():.2f}")
    macro("CtrlMemPaper", f"{memd['asan'].sum()/memd['base'].sum():.2f}")
    for b in common:
        macro(f"CtrlDef{mname(b)}", f"{res['asan-default'][0]['mean'][b]:.2f}")
        macro(f"CtrlPap{mname(b)}", f"{res['asan'][0]['mean'][b]:.2f}")
        macro(f"CtrlMemDef{mname(b)}", f"{memd['asan-default'][b]/memd['base'][b]:.2f}")
    macro("CtrlMemDefMax", f"{(memd['asan-default']/memd['base']).max():.1f}")
    macro("CtrlMemDefMaxName", (memd['asan-default']/memd['base']).idxmax())
    macro("CtrlDefDelta", f"{res['asan-default'][1][0]-res['asan'][1][0]:.2f}")
    macro("CtrlLeanDelta", f"{res['asan'][1][0]-res['asanlean'][1][0]:.2f}")


# ---------------------------------------------------------------- extension
def redzone(alloc):
    df = load("redzone")
    if df is None:
        return
    macro("RzRuns", df.rep.nunique())
    sizes = [16, 32, 64, 128, 256]
    tim = {s: summarize(ratios(df, f"rz{s}")) for s in sizes}
    memr = {s: summarize(ratios(df, f"rz{s}", "vmhwm")) for s in sizes}
    memm = df.groupby(["bench", "variant"]).vmhwm.mean().unstack()
    t = pd.DataFrame({f"time_rz{s}": tim[s][0]["mean"] for s in sizes} | {f"mem_rz{s}": memr[s][0]["mean"] for s in sizes})
    t.to_csv(SUM / "redzone.csv")
    rows = []
    for b in [b for b in tim[16][0].index if all(b in tim[s][0].index for s in sizes)]:
        rows.append([f"\\texttt{{{b}}}"] + [f"{tim[s][0]['mean'][b]:.2f}" for s in sizes] + [f"{memr[s][0]['mean'][b]:.2f}" for s in (16, 128, 256)])
    rows.append("MIDRULE")
    rows.append(["Average"] + [pm(*tim[s][1]) for s in sizes] + [f"{memm[f'rz{s}'].sum()/memm['base'].sum():.2f}" for s in (16, 128, 256)])
    tex_table("tab_redzone.tex", ["Benchmark"] + [f"T rz{s}" for s in sizes] + ["M rz16", "M rz128", "M rz256"], rows, "l" + "r" * 8)
    W = {16: "sixteen", 32: "thirtytwo", 64: "sixtyfour", 128: "onetwentyeight", 256: "twofiftysix"}
    for s in sizes:
        macro(f"RzT{W[s]}", f"{tim[s][1][0]:.2f}"); macro(f"RzT{W[s]}sd", f"{tim[s][1][1]:.2f}")
        macro(f"RzM{W[s]}", f"{memm[f'rz{s}'].sum()/memm['base'].sum():.2f}")
    d = (tim[256][0]["mean"] - tim[16][0]["mean"]).sort_values(ascending=False)
    macro("RzMostName", d.index[0]); macro("RzMostTsixteen", f"{tim[16][0]['mean'][d.index[0]]:.2f}")
    macro("RzMostTtwofiftysix", f"{tim[256][0]['mean'][d.index[0]]:.2f}")
    dm = (memr[256][0]["mean"] / memr[16][0]["mean"]).sort_values(ascending=False)
    macro("RzMemMostName", dm.index[0]); macro("RzMemMostsixteen", f"{memr[16][0]['mean'][dm.index[0]]:.2f}")
    macro("RzMemMosttwofiftysix", f"{memr[256][0]['mean'][dm.index[0]]:.2f}")

    fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.9))
    for i, b in enumerate(tim[16][0].index):
        c = plt.cm.tab20(i * 2 % 20 + i * 2 // 20)
        axs[0].plot(sizes, [tim[s][0]["mean"][b] for s in sizes], marker=".", lw=0.8, color=c, label=b)
        axs[1].plot(sizes, [memr[s][0]["mean"][b] for s in sizes], marker=".", lw=0.8, color=c)
    axs[0].plot(sizes, [tim[s][1][0] for s in sizes], color="black", lw=2, label="average")
    axs[1].plot(sizes, [memm[f"rz{s}"].sum() / memm["base"].sum() for s in sizes], color="black", lw=2)
    for a, lab in zip(axs[:2], ["slowdown vs. base", "peak RSS increase (x)"]):
        a.set_xscale("log", base=2); a.set_xticks(sizes); a.set_xticklabels(sizes); a.set_xlabel("min. heap redzone (bytes)")
        a.set_ylabel(lab); a.grid(lw=0.3)
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=6, fontsize=6, frameon=False)
    if alloc is not None:
        sens = (tim[256][0]["mean"] - tim[16][0]["mean"])
        msens = memr[256][0]["mean"] / memr[16][0]["mean"]
        a = alloc.reindex(sens.index)
        axs[2].scatter(a["small_per_s"], msens, s=10)
        for b in msens.index:
            axs[2].annotate(b, (a["small_per_s"][b], msens[b]), fontsize=5)
        axs[2].set_xscale("log"); axs[2].set_xlabel("allocs <=64 B per second (base)")
        axs[2].set_ylabel("peak RSS(rz256) / peak RSS(rz16)"); axs[2].grid(lw=0.3)
        macro("RzSpearman", f"{a['small_per_s'].rank().corr(sens.rank()):.2f}")
        macro("RzMemSpearman", f"{a['small_per_s'].rank().corr(msens.rank()):.2f}")
        flat = msens[msens < 1.05].index
        macro("RzMemFlat", len(flat))
    fig.tight_layout(rect=(0, 0.12, 1, 1)); fig.savefig(FIG / "fig_redzone.pdf"); plt.close(fig)
    return
    fig.tight_layout(); fig.savefig(FIG / "fig_redzone.pdf"); plt.close(fig)


# ---------------------------------------------------------------- allocation profile / binary size
def alloc_profile():
    f = RAW / "malloc-profile" / "profile.jsonl"
    if not f.exists():
        return None
    rows = []
    main = load("main")
    basewall = main[main.variant == "base"].groupby("bench").wall.mean() if main is not None else None
    for line in f.read_text().splitlines():
        r = json.loads(line); m = r["malloc"]
        w = basewall[r["bench"]] if basewall is not None else r["wall_s"]
        rows.append(dict(bench=r["bench"], allocs=m.get("allocs", 0), bytes=m.get("bytes", 0),
                         small=m.get("le16", 0) + m.get("le64", 0), allocs_per_s=m.get("allocs", 0) / w,
                         small_per_s=(m.get("le16", 0) + m.get("le64", 0)) / w))
    a = pd.DataFrame(rows).set_index("bench")
    a.to_csv(SUM / "malloc_profile.csv")
    return a


def binsize():
    f = RAW / "binsize" / "binsize.jsonl"
    if not f.exists():
        return
    d = pd.DataFrame([json.loads(l) for l in f.read_text().splitlines()])
    main_exe = {"bzip2": "bzip2", "perl": "miniperl", "lua": "lua", "sqlite": "speedtest1", "gnugo": "gnugo",
                "hmmer": "hmmsearch", "stockfish": "stockfish", "x264": "x264", "libxml2": "xmllint",
                "lulesh": "lulesh2.0", "tramp3d": "tramp3d-v4"}
    empty = d[d.bench == "_empty"].set_index("build")["text"]
    rt = int(empty["asan"] - empty["base"])          # .text added by the static ASan run-time
    nnue = int(d[(d.bench == "stockfish") & (d.exe == "_embedded_nnue")]["text"].sum())
    d = d[d.apply(lambda r: main_exe.get(r.bench) == r.exe, axis=1)]
    p = d.pivot(index="bench", columns="build", values="file_bytes")
    t = d.pivot(index="bench", columns="build", values="text").astype(float)
    t.loc["stockfish"] -= nnue                        # embedded data, identical in both builds
    ratio = p["asan"] / p["base"]; tratio = t["asan"] / t["base"]
    code = (t["asan"] - rt) / t["base"]               # instrumented program code only
    pd.DataFrame({"file_ratio": ratio, "text_ratio": tratio, "code_ratio_wo_runtime": code}).to_csv(SUM / "binsize.csv")
    macro("BinMin", f"{ratio.min():.1f}"); macro("BinMax", f"{ratio.max():.1f}"); macro("BinAvg", f"{ratio.mean():.1f}")
    macro("CodeMin", f"{code.min():.1f}"); macro("CodeMax", f"{code.max():.1f}"); macro("CodeAvg", f"{code.mean():.1f}")
    macro("RuntimeKB", f"{rt/1024:.0f}"); macro("NnueMB", f"{nnue/1e6:.0f}")
    rows = [[f"\\texttt{{{b}}}", f"{t['base'][b]/1024:.0f}", f"{t['asan'][b]/1024:.0f}", f"{tratio[b]:.2f}", f"{code[b]:.2f}"]
            for b in ORDER if b in t.index]
    rows.append("MIDRULE")
    rows.append(["Average", "", "", f"{tratio.mean():.2f}", f"{code.mean():.2f}"])
    tex_table("tab_binsize.tex", ["Benchmark", "Base .text [KB]", "ASan .text [KB]", "Increase", "Excl. run-time"], rows, "lrrrr")


def alloc_table(a, per_rw):
    if a is None or per_rw is None:
        return
    rows = []
    for b in [b for b in ORDER if b in a.index]:
        rows.append([f"\\texttt{{{b}}}", f"{a['allocs'][b]:,.0f}", f"{a['allocs_per_s'][b]:,.0f}",
                     f"{a['small'][b]/max(a['allocs'][b],1)*100:.0f}\\%", f"{per_rw['mean'][b]:.2f}"])
    tex_table("tab_alloc.tex", ["Benchmark", "Heap allocations", "Allocs/s", "$\\le$64 B", "Slowdown R+W"], rows, "lrrrr")
    rho = a["allocs_per_s"].reindex(per_rw.index).rank().corr(per_rw["mean"].rank())
    macro("AllocSpearman", f"{rho:.2f}")
    main = load("main")
    wo = summarize(ratios(main, "asanwo"))[0]["mean"]
    macro("AllocSpearmanWO", f"{a['allocs_per_s'].reindex(wo.index).rank().corr(wo.rank()):.2f}")
    # share of the R+W overhead that remains when reads are not checked
    share = (wo - 1) / (per_rw["mean"] - 1)
    hi = a["allocs_per_s"] > 1e6
    macro("WOShareHi", f"{share[hi.reindex(share.index)].mean()*100:.0f}")
    macro("WOShareLo", f"{share[~hi.reindex(share.index)].mean()*100:.0f}")
    macro("NumHiAlloc", int(hi.sum()))
    for b in a.index:
        macro(f"Allocs{mname(b)}", f"{a['allocs_per_s'][b]/1e6:.1f}")


def main():
    per_rw = main_experiment()
    controls()
    a = alloc_profile()
    alloc_table(a, per_rw)
    redzone(a)
    binsize()
    env = ROOT / "results" / "env.txt"
    (GEN / "macros.tex").write_text("".join(f"\\newcommand{{\\{k}}}{{{v}}}\n" for k, v in sorted(MACROS.items())))
    for k, v in sorted(MACROS.items()):
        print(f"  {k:18s} {v}")
    print(f"[analyze] wrote {SUM}, {GEN}, {FIG}")


if __name__ == "__main__":
    main()
