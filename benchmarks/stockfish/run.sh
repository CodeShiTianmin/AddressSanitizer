# Built-in bench: 16 MB hash, 1 thread, fixed depth 14 over the default positions.
"$BIN/stockfish" bench 16 1 14 default depth > "$OUT/sf.out" 2>&1
