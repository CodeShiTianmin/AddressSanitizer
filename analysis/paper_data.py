"""Numbers reported in Serebryany et al., USENIX ATC 2012.

FIG2_* : slowdown (instrumented / clang -O2 run time) digitized from the bar
         chart in Figure 2 (read off the 1.00-2.75 axis; resolution about +-0.03).
         The two values printed in the text are exact: perlbench 2.60x,
         xalancbmk 2.67x; average 1.73x (reads+writes), 1.26x (writes only).
TABLE1 : memory usage, MB (VmPeak at exit), Table 1.
TABLE2 : stack size, KB (VmStk at exit), Table 2.
"""
FIG2_RW = {"400.perlbench": 2.60, "401.bzip2": 1.83, "403.gcc": 1.55, "429.mcf": 1.91, "445.gobmk": 1.69,
           "456.hmmer": 1.80, "458.sjeng": 1.60, "462.libquantum": 1.08, "464.h264ref": 1.46,
           "471.omnetpp": 1.40, "473.astar": 1.63, "483.xalancbmk": 2.67, "433.milc": 1.50, "444.namd": 1.68,
           "447.dealII": 2.04, "450.soplex": 1.56, "453.povray": 2.00, "470.lbm": 1.42, "482.sphinx3": 1.57}
FIG2_WO = {"400.perlbench": 2.19, "401.bzip2": 1.26, "403.gcc": 1.22, "429.mcf": 1.10, "445.gobmk": 1.22,
           "456.hmmer": 1.25, "458.sjeng": 1.24, "462.libquantum": 1.00, "464.h264ref": 1.20,
           "471.omnetpp": 1.13, "473.astar": 1.17, "483.xalancbmk": 1.85, "433.milc": 1.17, "444.namd": 1.08,
           "447.dealII": 1.42, "450.soplex": 1.23, "453.povray": 1.43, "470.lbm": 1.00, "482.sphinx3": 1.05}
PAPER_AVG_RW, PAPER_AVG_WO = 1.73, 1.26          # Section 4 text ("73%", "26%")
TABLE1 = {"400.perlbench": (670, 2168), "401.bzip2": (858, 1618), "403.gcc": (893, 4133), "429.mcf": (1684, 2098),
          "445.gobmk": (37, 369), "456.hmmer": (33, 582), "458.sjeng": (180, 249), "462.libquantum": (104, 930),
          "464.h264ref": (72, 439), "471.omnetpp": (181, 787), "473.astar": (343, 1214), "483.xalancbmk": (434, 1688),
          "433.milc": (694, 1618), "444.namd": (58, 146), "447.dealII": (807, 2602), "450.soplex": (637, 2479),
          "453.povray": (17, 371), "470.lbm": (417, 550), "482.sphinx3": (52, 426)}
PAPER_MEM_TOTAL = 3.37                           # Table 1, "total" row (24467 / 8171 MB)
TABLE2 = {"400.perlbench": (568, 1740), "445.gobmk": (184, 264), "458.sjeng": (828, 848),
          "483.xalancbmk": (2116, 4720), "453.povray": (88, 96), "482.sphinx3": (248, 252)}
PAPER_BINSIZE = (1.5, 3.2, 2.5)                  # min, max, average binary size increase (text)

# Our open-source workload -> SPEC CPU2006 counterpart (None = no counterpart).
COUNTERPART = {"perl": "400.perlbench", "bzip2": "401.bzip2", "gnugo": "445.gobmk", "hmmer": "456.hmmer",
               "stockfish": "458.sjeng", "x264": "464.h264ref", "libxml2": "483.xalancbmk",
               "tramp3d": "447.dealII", "lulesh": "433.milc", "lua": None, "sqlite": None}
RELATION = {"perl": "same program, newer release", "bzip2": "same program, newer release",
            "gnugo": "same program, newer release", "hmmer": "same program, newer major version",
            "stockfish": "same domain (chess engine)", "x264": "same domain (H.264 encoder)",
            "libxml2": "same domain (XML processing)", "tramp3d": "same domain (C++ template FP)",
            "lulesh": "same domain (FP stencil/physics)", "lua": "extra (interpreter)", "sqlite": "extra (database)"}

# Counterparts that are the same program or the same application domain; the
# "7 counterparts" averages use only these (tramp3d/lulesh are loose analogues).
STRICT = ["perl", "bzip2", "gnugo", "hmmer", "stockfish", "x264", "libxml2"]
