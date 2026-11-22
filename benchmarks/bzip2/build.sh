tar xzf "$DL/bzip2-1.0.8.tar.gz" --strip-components=1
make -j"$JOBS" CC="$CC" CFLAGS="$CFLAGS -D_FILE_OFFSET_BITS=64" LDFLAGS="$LDFLAGS" bzip2
cp bzip2 "$BIN/"
