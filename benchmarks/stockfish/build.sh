# Chess engine (stand-in for 458.sjeng). NNUE networks are embedded at compile time.
tar xzf "$DL/stockfish-sf_16.1.tar.gz" --strip-components=1
cp "$DL"/nn-*.nnue src/
make -C src -j"$JOBS" build ARCH=x86-64-avx2 COMP=clang CXX="$CXX" optimize=no \
     EXTRACXXFLAGS="$CXXFLAGS" EXTRALDFLAGS="$LDFLAGS"
cp src/stockfish "$BIN/"
