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
$ git clone git@github.com:SeanHeelan/PHP-SHRIKE.git
$ cd PHP-SHRIKE
$ ./buildconf -f
$ ./configure --prefix=`pwd`/install --enable-shrike --enable-dve \
	--enable-mbstring --enable-intl --enable-exif --with-gd
$ make && make install
```

Now we need to extract the tests that come with PHP. These are standalone PHP
scripts that test functionality, regressions and so on.

```
$ cd PHP-SHRIKE
$ export TEST_PHP_EXECUTABLE=`pwd`/install/bin/php
$ ./install/bin/php ./run-tests.php -x --offline --keep-php \
	--temp-target phptests --temp-source `pwd`
$ # Clean up some files we don't need
$ find phptests/ -regex ".*\(phpt\|skip\).phps" | xargs rm
$ # This should leave just under 12k files
$ find phptests/ -name *.phps | wc -l
```

### Extracting Valid Fragments of PHP

Add the directory containing `shrike` to your Python path. Assuming you have
cloned the `HeapLayout` repository at `~/HeapLayout`, one way to do this is as
follows:

```
$ echo 'export PYTHONPATH=~/HeapLayout/Shrike:$PYTHONPATH' >> ~/.bashrc
$ source ~/.bashrc
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
$ ./fuzz.py -p PHP-SHRIKE/install/bin/php fragged.pkl -t N
INFO:__main__:Utilising 6 cores
INFO:__main__:Analysing the PHP binary at PHP-SHRIKE/install/bin/php
INFO:__main__:278 unique sequences across 490 fragments loaded from fragged.pkl
INFO:shrike.php7:9200 total executions (153.33333333333334 per second)
INFO:shrike.php7:2940 duplicates discovered
INFO:shrike.php7:4520 errors
INFO:__main__:1740 new interaction sequence discovered
INFO:__main__:Writing fuzzing results to fuzzed_fragged.pkl
```

### Template-Based Exploit Development with SHRIKE

SHRIKE enables what I have taken to calling 'template-based exploit
development'. The concept is explained in a bit more detail in [this][3] blog
post. Essentially, the exploit developer writes their exploit as normal but
leaves 'holes' in the exploit where a heap layout problem needs to be solved.
SHRIKE then takes this 'template' and fills in the holes, such that the layout
desired by the exploit developer is achieved. It's obviously very early days
yet, and I have only implemented the concept for PHP, but I think it's a
promising direction for the addition of automation to exploitation.

The `solve.py` script is responsible for taking a template, as well as the PHP
fragments we discovered above, and trying to solve the layout problems embedded
in the template. The script operates by rewriting the templates to insert PHP
fragments and then handing them off to our custom version of PHP, which contains
helper functions for things like recording allocation addresses. It then
iterates this process until a solution is found.

Lets have a look at an example, which should hopefully clarify
things. For full details see section 3.2 of the paper.

In the `templates` directory you will find a number of templates, which are just
normal PHP scripts but with directives starting with `#X-SHRIKE`. These
directives are used to inform SHRIKE of the details of the layout problem to be
solved. For example, `templates/cve-2013-2110-hash_init.template.php` contains
the following lines:

```php
<?php

...

$quote_str = str_repeat("\xf4", 123);
#X-SHRIKE HEAP-MANIP 384 32
# Allocates a 32 byte buffer as its third allocation
#X-SHRIKE RECORD-ALLOC 2 1
$vtx_dst = hash_init("md5");
#X-SHRIKE HEAP-MANIP 384 32
#X-SHRIKE RECORD-ALLOC 0 2
quoted_printable_encode($quote_str);
#X-SHRIKE REQUIRE-DISTANCE 1 2 384

...
?>
```

The directives operate as follows (full details in section 3.2.3 of the paper):

* The `HEAP-MANIP` directive is followed by one or more integers, telling SHRIKE
  that at this point it should insert fragments that make allocations with size
  equal to one of these integers.

* The `RECORD-ALLOC` directive tells SHRIKE to insert a call to a function we
  have inserted into PHP that records the address of an allocation about to take
  place. `RECORD-ALLOC X Y` tells SHRIKE to record the Xth allocation and give
  it the ID Y. Allocation indices start from 0.

* The `REQUIRE-DISTANCE X Y Z` directive tells SHRIKE to insert code to check if
  the distance between allocation with ID X and the allocation with ID Y is
  equal to Z.

A template can contain as many `REQUIRE-DISTANCE` directives as you like. SHRIKE
will start from the first and solve them one after the other.

solve.py
demo

extras - controlled_gen.py
extras - pointer_search.py


[1]: https://sean.heelan.io/heaplayout
[2]: https://github.com/SeanHeelan/PHP-SHRIKE
[3]: https://sean.heelan.io
