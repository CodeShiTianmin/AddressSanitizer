#!/usr/bin/env python3
"""Generate the deterministic benchmark inputs into data/ (seeded, no network access).

Inputs that are derived from the pinned source archives (text corpora) are
extracted from downloads/; synthetic inputs (protein database, video, XML)
are produced from a fixed random seed so every machine gets identical bytes.
"""
import gzip, hashlib, os, random, sys, tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DL, DATA = ROOT / "downloads", ROOT / "data"
SEED = 340


def corpus_from_perl_tarball(out: Path, limit: int):
    """Concatenate the text members (.pod/.pm/.c/.h) of the perl tarball."""
    buf = bytearray()
    with tarfile.open(DL / "perl-5.38.2.tar.gz") as tf:
        for m in sorted(tf.getmembers(), key=lambda m: m.name):
            if m.isfile() and m.name.endswith((".pod", ".pm", ".c", ".h")):
                buf += tf.extractfile(m).read()
                if len(buf) >= limit:
                    break
    out.write_bytes(bytes(buf[:limit]))


def bzip2_input(out: Path, size=24 << 20):
    """Half text (perl sources), half pseudo-random structured binary."""
    rng = random.Random(SEED)
    tmp = out.with_suffix(".txt")
    corpus_from_perl_tarball(tmp, size // 2)
    text = tmp.read_bytes(); tmp.unlink()
    words = [bytes(rng.getrandbits(8) for _ in range(rng.randint(2, 12))) for _ in range(4096)]
    binary = bytearray()
    while len(binary) < size - len(text):
        binary += rng.choice(words)
    out.write_bytes(text + bytes(binary[: size - len(text)]))


def protein_db(out: Path, nseq=8000, length=(150, 500)):
    rng = random.Random(SEED)
    aa = "ACDEFGHIKLMNPQRSTVWY"
    freq = [8.25, 1.37, 5.45, 6.75, 3.86, 7.07, 2.27, 5.96, 5.84, 9.66,
            2.42, 4.06, 4.70, 3.93, 5.53, 6.56, 5.34, 6.87, 1.08, 2.92]
    with out.open("w") as f:
        for i in range(nseq):
            n = rng.randint(*length)
            seq = "".join(rng.choices(aa, weights=freq, k=n))
            f.write(f">seq{i}\n")
            for j in range(0, n, 60):
                f.write(seq[j:j + 60] + "\n")


def video_y4m(out: Path, w=352, h=288, frames=150):
    """CIF-sized synthetic clip: moving gradients and blocks plus mild noise."""
    import numpy as np
    rng = np.random.default_rng(SEED)
    yy, xx = np.mgrid[0:h, 0:w]
    with out.open("wb") as f:
        f.write(f"YUV4MPEG2 W{w} H{h} F25:1 Ip A1:1 C420jpeg\n".encode())
        for t in range(frames):
            y = (128 + 60 * np.sin((xx + 3 * t) / 23.0) * np.cos((yy - 2 * t) / 31.0)).astype(np.int16)
            for k in range(6):
                bx, by = (40 + 50 * k + 4 * t) % (w - 48), (30 + 37 * k + 3 * t * (k % 3 - 1)) % (h - 48)
                y[by:by + 48, bx:bx + 48] = 40 + 35 * k
            y = np.clip(y + rng.integers(-6, 7, size=y.shape), 0, 255).astype(np.uint8)
            u = np.full((h // 2, w // 2), 128, np.uint8) + ((xx[::2, ::2] + t) % 64).astype(np.uint8) // 4
            v = np.full((h // 2, w // 2), 128, np.uint8) - ((yy[::2, ::2] + t) % 64).astype(np.uint8) // 4
            f.write(b"FRAME\n" + y.tobytes() + u.astype(np.uint8).tobytes() + v.astype(np.uint8).tobytes())


def xml_doc(out: Path, items=200000):
    rng = random.Random(SEED)
    words = ["alpha", "beta", "gamma", "delta", "kernel", "page", "inode", "sched", "mutex",
             "buffer", "cache", "shadow", "redzone", "quarantine", "heap", "stack", "&amp;", "&lt;x&gt;"]
    with out.open("w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<catalog xmlns:m="urn:meta">\n')
        for i in range(items):
            t = rng.choice("abcde")
            f.write(f'  <item id="i{i}" type="{t}" price="{rng.uniform(1, 999):.2f}">\n')
            f.write(f'    <name>{" ".join(rng.choices(words, k=rng.randint(2, 6)))}</name>\n')
            f.write(f'    <m:tags>{"".join(f"<tag>{w}</tag>" for w in rng.choices(words, k=rng.randint(1, 5)))}</m:tags>\n')
            if rng.random() < 0.3:
                f.write(f'    <![CDATA[{" ".join(rng.choices(words, k=12))}]]>\n')
            f.write("  </item>\n")
        f.write("</catalog>\n")


def main():
    DATA.mkdir(exist_ok=True)
    jobs = {
        "bzip2.in": bzip2_input,
        "perl_corpus.txt": lambda p: corpus_from_perl_tarball(p, 6 << 20),
        "proteins.fa": protein_db,
        "clip.y4m": video_y4m,
        "catalog.xml": xml_doc,
    }
    for name, fn in jobs.items():
        p = DATA / name
        if not p.exists() or "--force" in sys.argv:
            print(f"[inputs] generating {name}")
            fn(p)
        print(f"[inputs] {name:16s} {p.stat().st_size:>10d} B  sha256={hashlib.sha256(p.read_bytes()).hexdigest()[:16]}")


if __name__ == "__main__":
    main()
