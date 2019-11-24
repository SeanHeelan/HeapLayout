#!/bin/sh

set -e

install_dir="$(pwd)/install-asan"
make clean

./configure --prefix="$install_dir" \
    --enable-zip --enable-shrike --enable-dve --enable-mbstring --enable-intl \
    --enable-exif --with-gd --with-bz2 CXXFLAGS="-DU_USING_ICU_NAMESPACE=1 "\
    CFLAGS="-DU_USING_ICU_NAMESPACE=1 -O0 -g -fsanitize=address" \
    LDFLAGS="-L/data/Documents/git/ShapeShifter/libshapeshifter" \
    LIBS="-ldummyssr"

make -j 5

make install
