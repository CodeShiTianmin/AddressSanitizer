# Build a profile HMM from the protein-kinase alignment and search a seeded random database
# with all acceleration filters off (--max), so the full Viterbi/Forward DP kernels run.
"$BIN/hmmbuild" "$OUT/pk.hmm" "$BIN/Pkinase.sto" > /dev/null
"$BIN/hmmsearch" --max -o "$OUT/hmmsearch.out" "$OUT/pk.hmm" "$DATA/proteins.fa"
