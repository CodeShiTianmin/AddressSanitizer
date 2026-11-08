# compress at -9 (900k blocks) then decompress, both in memory -> /dev/null via pipe-free files
"$BIN/bzip2" -9 -c "$DATA/bzip2.in" > "$OUT/x.bz2"
"$BIN/bzip2" -d -c "$OUT/x.bz2" > "$OUT/x.out"
cmp -s "$DATA/bzip2.in" "$OUT/x.out"
