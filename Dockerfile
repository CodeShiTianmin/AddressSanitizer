# Pinned experiment environment for the AddressSanitizer (USENIX ATC'12) replication.
# Base image pinned by digest; the compiler is pinned to an exact package version.
FROM ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852

ARG DEBIAN_FRONTEND=noninteractive
ARG CLANG_PKG_VERSION=1:18.1.3-1ubuntu1

RUN apt-get update && apt-get install -y --no-install-recommends \
        clang-18=${CLANG_PKG_VERSION} \
        libclang-rt-18-dev=${CLANG_PKG_VERSION} \
        llvm-18=${CLANG_PKG_VERSION} \
        make cmake autoconf automake libtool pkg-config \
        time util-linux procps wget curl ca-certificates unzip xz-utils bzip2 \
        file less python3 python3-numpy python3-pandas python3-matplotlib \
        texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/clang-18 /usr/local/bin/clang \
    && ln -sf /usr/bin/clang++-18 /usr/local/bin/clang++ \
    && ln -sf /usr/bin/llvm-symbolizer-18 /usr/local/bin/llvm-symbolizer

ENV CC=clang CXX=clang++ LC_ALL=C.UTF-8
WORKDIR /work
CMD ["bash"]
