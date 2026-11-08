# GTP self-play on a 13x13 board (445.gobmk also drives GNU Go through GTP scripts).
"$BIN/gnugo" --mode gtp --quiet --level 8 --seed 1 < "$BENCH_DIR/selfplay.gtp" > "$OUT/gnugo.out"
