# miniperl = the full perl interpreter without dynamic loading (like the statically
# linked 400.perlbench); the workload only uses core features.
tar xzf "$DL/perl-5.38.2.tar.gz" --strip-components=1
./Configure -des -Dcc="$CC" -Doptimize="$CFLAGS" -Dldflags="$LDFLAGS" -Dlddlflags="-shared $LDFLAGS" \
            -Dprefix="$WORK/inst" -Uusedevel -Uusethreads
make -j"$JOBS" miniperl
cp miniperl "$BIN/"
