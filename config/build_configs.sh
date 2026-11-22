# Compiler flag sets ("build configurations"). Sourced by scripts/build.sh.
# Every configuration uses the same optimisation level as the paper's baseline (clang -O2).
# usage: set_build_config <name>   -> exports CFLAGS/CXXFLAGS/LDFLAGS
OPT="-O2"
set_build_config() {
  case "$1" in
    base)      FLAGS="$OPT" ; LFLAGS="" ;;
    # ASan, reads and writes instrumented (paper, Figure 2 "reads and writes")
    asan)      FLAGS="$OPT -fsanitize=address" ; LFLAGS="-fsanitize=address" ;;
    # ASan, only writes instrumented (paper, Figure 2 "writes only")
    asanwo)    FLAGS="$OPT -fsanitize=address -mllvm -asan-instrument-reads=false" ; LFLAGS="-fsanitize=address" ;;
    # Controlled re-run: switch off instrumentation features added after 2012
    # (stack-use-after-return fake stacks, use-after-scope poisoning).
    asanlean)  FLAGS="$OPT -fsanitize=address -fsanitize-address-use-after-return=never -fno-sanitize-address-use-after-scope" ; LFLAGS="-fsanitize=address" ;;
    *) echo "unknown build config: $1" >&2; return 1 ;;
  esac
  export CFLAGS="$FLAGS" CXXFLAGS="$FLAGS" LDFLAGS="$LFLAGS"
}
BUILD_CONFIGS="base asan asanwo asanlean"
