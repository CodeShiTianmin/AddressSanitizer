unzip -q "$DL/sqlite-amalgamation-3460000.zip"
cd sqlite-amalgamation-3460000
cp "$DL/speedtest1.c" .
$CC $CFLAGS -DSQLITE_THREADSAFE=0 -DSQLITE_OMIT_LOAD_EXTENSION -I. speedtest1.c sqlite3.c \
    -o "$BIN/speedtest1" $LDFLAGS -lm
