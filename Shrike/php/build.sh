#!/bin/sh

set -e

install_dir="$(pwd)/install"
make clean

./configure --prefix="$install_dir" \
    --enable-zip --enable-shrike --enable-dve --enable-mbstring --enable-intl \
    --enable-exif --with-gd CXXFLAGS="-DU_USING_ICU_NAMESPACE=1 "\
    CFLAGS="-DU_USING_ICU_NAMESPACE=1 -O2" \
    LDFLAGS="-L/data/Documents/git/ShapeShifter/libshapeshifter" \
    LIBS="-ldummyssr"

make -j 5

make install
