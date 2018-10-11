# Shrike

See the [associated paper][1].

## Install

### Python Dependencies

Python 3.6 or higher is required. Assuming you have it available as `python36`
on your system, the following will initialise the required virtual environment.

```
$ virtualenv --python36 shrike-venv
$ source shrike-venv/bin/activate
$ pip install -r requirements.txt
```

## Usage

### Dumping PHP's Tests

First we need to build our customised version of [PHP][2]. This is a modified
version of PHP 7.1.6. The primary modifications are the addition of a number of
vulnerabilities that were patched in previous versions, as well as an extension
which adds new functions to PHP required by Shrike. Namely, functions that can
record pointers and produce the distance between two recorded allocations.

```
git clone git@github.com:SeanHeelan/PHP-SHRIKE.git
cd PHP-SHRIKE
./buildconf -f
./configure --prefix=`pwd`/install --enable-shrike --enable-dve \
	--enable-mbstring --enable-intl --enable-exif --with-gd
make && make install
```

Now we need to extract the tests that come with PHP. These are standalone PHP
scripts that test functionality, regressions and so on.

```
cd PHP-SHRIKE
export TEST_PHP_EXECUTABLE=`pwd`/install/bin/php
./install/bin/php ./run-tests.php -x --offline --keep-php \
	--temp-target phptests --temp-source `pwd`
# Clean up some files we don't need
find phptests/ -regex ".*\(phpt\|skip\).phps" | xargs rm
# This should leave just under 12k files
find phptests/ -name *.phps | wc -l
```

### Extracting Valid Fragments of PHP

Add the directory containing `shrike to your Python path. Assuming you have
cloned the `HeapLayout` repository at `~/HeapLayout`, one way to do this is as
follows:

```
echo 'export PYTHONPATH=~/HeapLayout/Shrike:$PYTHONPATH' >> ~/.bashrc
source ~/.bashrc
```

We can then extract fragments of valid PHP from these tests as follows:

```
$ ./frag.py -o fragged.pkl -p PHP-SHRIKE/install/bin/php phptests/
INFO:__main__:Utilising 6 cores
INFO:__main__:Analysing the PHP binary at PHP-SHRIKE/install/bin/php
INFO:__main__:Processing tests from phptests/
INFO:shrike.php7:Processed 11878 files
INFO:shrike.php7:No results from 8757 files
INFO:shrike.php7:203 extracted functions
INFO:__main__:Extracting sequences from 1626 fragments
INFO:__main__:89/1626 tests contained fatal errors
INFO:__main__:1/1626 tests triggered OS errors
INFO:__main__:87/1626 tests contained disabled functions
INFO:__main__:959/1626 tests triggered no heap interaction
INFO:__main__:278 unique allocator interaction sequences out of 490 total
INFO:__main__:Logging sequences to fragged.pkl
```

### Fuzzing Fragments

From running the tests we have discovered nearly 300 interaction sequences with
heap allocator. We can find many more by fuzzing the existing fragments. Replace
the `N` in the command line with the number of seconds you wish to fuzz for.
With a single core you should give it 30 minutes (1800 seconds) or so. If you
have more cores available this can be reduced. The output shown is for 60
seconds with 6 cores, but you will want to let it run for longer.

```
$ ./fuzz.py -p PHP-SHRIKE/install/bin/php fragged.pkl -t 60
INFO:__main__:Utilising 6 cores
INFO:__main__:Analysing the PHP binary at PHP-SHRIKE/install/bin/php
INFO:__main__:278 unique sequences across 490 fragments loaded from fragged.pkl
INFO:shrike.php7:9200 total executions (153.33333333333334 per second)
INFO:shrike.php7:2940 duplicates discovered
INFO:shrike.php7:4520 errors
INFO:__main__:1740 new interaction sequence discovered
INFO:__main__:Writing fuzzing results to fuzzed_fragged.pkl
```

solve.py
demo

extras - controlled_gen.py
extras - pointer_search.py


[1]: https://sean.heelan.io/heaplayout
[2]: https://github.com/SeanHeelan/PHP-SHRIKE
