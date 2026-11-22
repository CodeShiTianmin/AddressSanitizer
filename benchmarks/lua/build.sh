tar xzf "$DL/lua-5.4.6.tar.gz" --strip-components=1
make -C src -j"$JOBS" CC="$CC" CFLAGS="$CFLAGS -Wall -DLUA_COMPAT_5_3 -DLUA_USE_LINUX" \
     MYLDFLAGS="$LDFLAGS" SYSLIBS="-Wl,-E -ldl" lua
cp src/lua "$BIN/"
