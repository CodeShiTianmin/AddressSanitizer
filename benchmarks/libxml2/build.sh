# XML parser/serializer (stand-in for 483.xalancbmk).
tar xJf "$DL/libxml2-2.12.9.tar.xz" --strip-components=1
./configure CC="$CC" CFLAGS="$CFLAGS" LDFLAGS="$LDFLAGS" --disable-shared --enable-static \
     --without-python --without-zlib --without-lzma --without-http --without-ftp --without-threads \
     --without-iconv --without-icu --without-readline
make -j"$JOBS" xmllint
cp xmllint "$BIN/"
