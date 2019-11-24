#!/usr/bin/env bash

./configure --prefix=`pwd`/install \
	--enable-shrike --enable-dve \
	--enable-mbstring --enable-intl --with-gd CFLAGS=-g

make -j 2
