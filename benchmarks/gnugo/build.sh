# GNU Go is the program behind SPEC CPU2006 445.gobmk. Its 2009 C code needs a few
# compatibility switches for clang 18 (identical in every configuration).
tar xzf "$DL/gnugo-3.8.tar.gz" --strip-components=1
COMPAT="-fcommon -Wno-error=implicit-function-declaration -Wno-error=implicit-int -Wno-error=int-conversion"
./configure CC="$CC" CFLAGS="$CFLAGS $COMPAT" LDFLAGS="$LDFLAGS" --without-readline --without-curses --disable-color
make -j"$JOBS"
cp interface/gnugo "$BIN/"
