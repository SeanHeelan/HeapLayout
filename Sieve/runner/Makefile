DISABLE_BUILTINS=-fno-builtin-malloc -fno-builtin-calloc -fno-builtin-realloc \
		 -fno-builtin-free

all: default tcm261 jem501 dlm286 avr2537 jem450

debug: all default-debug tcm261-debug jem501-debug dlm286-debug avr2537-debug \
	jem450-debug

default:
	gcc $(DISABLE_BUILTINS) -o runner runner.c

default-debug:
	gcc $(DISABLE_BUILTINS) -g -O0 -o runner-debug runner.c

tcm261:
	cd gperftools-2.6.1 && \
		./autogen.sh && \
		./configure --prefix=`pwd`/install --disable-shared && \
		make && make install
	g++ $(DISABLE_BUILTINS) -o runner-tcmalloc-2.6.1 runner.c \
		gperftools-2.6.1/install/lib/libtcmalloc_minimal.a -lpthread

tcm261-debug:
	g++ $(DISABLE_BUILTINS) -g -O0 -o runner-tcmalloc-2.6.1-debug runner.c \
		gperftools-2.6.1/install/lib/libtcmalloc_minimal.a -lpthread

jem450:
	cd jemalloc-4.5.0 && \
		./autogen.sh && \
		./configure --prefix=`pwd`/install && \
		make clean && make && make install
	export PATH=`pwd`/jemalloc-4.5.0/install/bin:$(PATH) && \
	gcc $(DISABLE_BUILTINS) -o runner-jemalloc-4.5.0 runner.c \
		jemalloc-4.5.0/install/lib/libjemalloc.a -lpthread -ldl

jem450-debug:
	cd jemalloc-4.5.0 && \
		./autogen.sh && \
		./configure --enable-debug --prefix=`pwd`/install-debug && \
		make clean && make && make install
	export PATH=`pwd`/jemalloc-4.5.0/install-debug/bin:$(PATH) && \
	gcc $(DISABLE_BUILTINS) -g -O0 -o runner-jemalloc-4.5.0-debug runner.c \
		jemalloc-4.5.0/install-debug/lib/libjemalloc.a -lpthread -ldl

jem501:
	cd jemalloc-5.0.1 && \
		./autogen.sh && \
		./configure --prefix=`pwd`/install && \
		make clean && make && make install
	export PATH=`pwd`/jemalloc-5.0.1/install/bin:$(PATH) && \
	gcc $(DISABLE_BUILTINS) -o runner-jemalloc-5.0.1 runner.c \
		jemalloc-5.0.1/install/lib/libjemalloc.a -lpthread -ldl

jem501-debug:
	cd jemalloc-5.0.1 && \
		./autogen.sh && \
		./configure --enable-debug --prefix=`pwd`/install-debug && \
		make clean && make && make install
	export PATH=`pwd`/jemalloc-5.0.1/install-debug/bin:$(PATH) && \
	gcc $(DISABLE_BUILTINS) -g -O0 -o runner-jemalloc-5.0.1-debug runner.c \
		jemalloc-5.0.1/install-debug/lib/libjemalloc.a -lpthread -ldl

dlm286:
	cd dlmalloc-2.8.6 && \
		gcc -o dlmalloc-2.8.6.o -c dlmalloc-2.8.6.c && \
		ar rcs libdlmalloc-2.8.6.a dlmalloc-2.8.6.o
	gcc $(DISABLE_BUILTINS) -o runner-dlmalloc-2.8.6 runner.c \
		dlmalloc-2.8.6/libdlmalloc-2.8.6.a

dlm286-debug:
	cd dlmalloc-2.8.6 && \
		gcc -g -O0 -o dlmalloc-2.8.6-debug.o -c dlmalloc-2.8.6.c && \
		ar rcs libdlmalloc-2.8.6-debug.a dlmalloc-2.8.6-debug.o
	gcc $(DISABLE_BUILTINS) -g -O0 -o runner-dlmalloc-2.8.6-debug runner.c \
		dlmalloc-2.8.6/libdlmalloc-2.8.6-debug.a

avr2537:
	cd avrlibc-r2537 && \
		gcc -o avrlibc-r2537.o -c avrmalloc.c && \
		ar rcs libavrlibc-r2537.a avrlibc-r2537.o
	gcc $(DISABLE_BUILTINS) -DCOUNTHOLES -o runner-avrlibc-r2537 runner.c \
		avrlibc-r2537/libavrlibc-r2537.a

avr2537-debug:
	cd avrlibc-r2537 && \
		gcc -g -O0 -o avrlibc-r2537-debug.o \
			-c avrmalloc.c && \
		ar rcs libavrlibc-r2537-debug.a avrlibc-r2537-debug.o
	gcc $(DISABLE_BUILTINS) -DCOUNTHOLES -g -O0 \
		-o runner-avrlibc-r2537-debug runner.c \
		avrlibc-r2537/libavrlibc-r2537-debug.a

exclusive-captures:
	cd avrlibc-r2537 && \
		gcc -o avrlibc-r2537.o -c avrmalloc.c && \
		ar rcs libavrlibc-r2537.a avrlibc-r2537.o
	gcc $(DISABLE_BUILTINS) -o count-ex-caps count_exclusive_captures.c \
		avrlibc-r2537/libavrlibc-r2537.a

exclusive-captures-debug:
	cd avrlibc-r2537 && \
		gcc -g -O0 -o avrlibc-r2537.o -c avrmalloc.c && \
		ar rcs libavrlibc-r2537.a avrlibc-r2537.o
	gcc $(DISABLE_BUILTINS) -g -O0 -o count-ex-caps-debug \
		count_exclusive_captures.c avrlibc-r2537/libavrlibc-r2537.a

clean:
	rm -f runner runner-jemalloc-5.0.1 \
		runner-debug runner-jemalloc-5.0.1-debug \
		runner-dlmalloc-2.8.6 runner-dlmalloc-2.8.6-debug \
		runner-tcmalloc-2.6.1 runner-tcmalloc-2.6.1-debug \
		runner-avrlibc-r2537 runner-avrlibc-r2537-debug
	cd dlmalloc-2.8.6 && rm -f *.o *.a
	cd avrlibc-r2537 && rm -f *.o *.a
	cd jemalloc-5.0.1 && make clean && make distclean
	cd jemalloc-4.5.0 && make clean && make distclean
	cd gperftools-2.6.1 && make clean && make distclean
