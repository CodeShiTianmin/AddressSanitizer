# LLNL hydrodynamics proxy app (C++, floating point). Serial build: no MPI, no OpenMP.
tar xzf "$DL/lulesh-2.0.3.tar.gz" --strip-components=1
$CXX $CXXFLAGS -DUSE_MPI=0 -I. lulesh.cc lulesh-comm.cc lulesh-viz.cc lulesh-util.cc lulesh-init.cc \
     -o "$BIN/lulesh2.0" $LDFLAGS -lm
