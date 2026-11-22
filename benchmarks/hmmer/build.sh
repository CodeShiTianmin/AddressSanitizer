tar xzf "$DL/hmmer-3.4.tar.gz" --strip-components=1
./configure CC="$CC" CFLAGS="$CFLAGS" LDFLAGS="$LDFLAGS" --disable-threads --disable-mpi
make -j"$JOBS"
cp src/hmmsearch src/hmmbuild easel/miniapps/esl-shuffle "$BIN/"
cp tutorial/Pkinase.sto tutorial/globins4.sto "$BIN/" 2>/dev/null || true
