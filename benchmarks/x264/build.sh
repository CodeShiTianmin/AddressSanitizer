# H.264 encoder (stand-in for 464.h264ref); hand-written assembly disabled so that
# all hot code is C and therefore instrumented, as in h264ref.
tar xjf "$DL/x264-31e19f92.tar.bz2" --strip-components=1
CC="$CC" ./configure --disable-asm --disable-opencl --disable-lavf --disable-swscale --disable-ffms \
     --disable-gpac --disable-lsmash --disable-thread --enable-static --bit-depth=8 \
     --extra-cflags="$CFLAGS" --extra-ldflags="$LDFLAGS"
make -j"$JOBS" x264
cp x264 "$BIN/"
