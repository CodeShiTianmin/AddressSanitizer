# Third-party software and credits

The paper under reproduction: K. Serebryany, D. Bruening, A. Potapenko, D. Vyukov,
"AddressSanitizer: A Fast Address Sanity Checker", USENIX ATC 2012.
AddressSanitizer is part of the LLVM project (compiler-rt), Apache-2.0 WITH LLVM-exception,
used unmodified via the Ubuntu `clang-18` package.

None of the programs below is redistributed in this repository; `scripts/fetch.sh`
downloads them from upstream (URLs and SHA-256 in `scripts/sources.txt`).

| Program | Version | License | Upstream |
|---|---|---|---|
| bzip2 | 1.0.8 | bzip2 license (BSD-style) | https://sourceware.org/bzip2/ |
| Perl | 5.38.2 | GPL-1.0+ or Artistic | https://www.perl.org/ |
| Lua | 5.4.6 | MIT | https://www.lua.org/ |
| SQLite (+ speedtest1.c) | 3.46.0 | Public domain | https://www.sqlite.org/ |
| GNU Go | 3.8 | GPL-3.0+ | https://www.gnu.org/software/gnugo/ |
| HMMER / Easel | 3.4 | BSD-3-Clause | http://hmmer.org/ |
| Stockfish (+ NNUE nets) | 16.1 | GPL-3.0 | https://stockfishchess.org/ |
| x264 | 31e19f92 | GPL-2.0+ | https://code.videolan.org/videolan/x264 |
| libxml2 | 2.12.9 | MIT | https://gitlab.gnome.org/GNOME/libxml2 |
| LULESH | 2.0.3 | BSD-style (LLNL) | https://github.com/LLNL/LULESH |
| tramp3d-v4 (LLVM test-suite) | llvmorg-18.1.8 | Apache-2.0 WITH LLVM-exception | https://github.com/llvm/llvm-test-suite |

The workload scripts `benchmarks/perl/workload.pl` and `benchmarks/lua/workload.lua`
were written by the group; the Lua kernels follow the well-known
Computer Language Benchmarks Game problem definitions.
