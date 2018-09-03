# Sieve

Sieve is a framework for setting up and running experiments for evaluating
algorithms for [heap layout manipulation][1]. The `runexp.py` script will run a
single experiment. See `repeat_experiments.sh` and `expmgmt.py` for scripts to
recreate the experiments described in the [associated paper][1].

## Install

### Python Dependencies

Python 3.6 or higher is required. Assuming you have it available as `python36`
on your system, the following will initialise the required virtual environment.

```
$ virtualenv --python36 sieve-venv
$ source sieve-venv/bin/activate
$ pip install -r requirements.txt
```

### Building the Allocator Drivers

```
cd runners
make
```

This should result in a number of binaries in the `runners` directory that act
as drivers for each of the allocators.

### Environment Variables

The environment variable `HEAP_STARTING_CONFIGS` must be set to the full path of
the `HeapLayout/Sieve/sieve/starting_configs` directory.

You must also add `HeapLayout/Sieve` to PYTHONPATH so that the `sieve` module
can be imported.

## Running an Experiment

Run `./runexp.py --help` to see a list of available parameters for
experimentation.

A layout experiment involves two allocations of interest. The `-f` parameter
indicates the size of the allocation to be made temporally first, while the `-s`
parameter indicates the size of the allocation to be made temporally second. The
goal of the search is to place these adjacent to each other. The search attempts
to solve for both possible layouts concurrently, i.e. the first allocation
before the second, and the first allocation after the second. In the output the
'neg. distance' is given by the location of the second allocation minus the
location of the first allocation minus the size of the second allocation.

Many allocators use inline metadata and thus it is not possible to have the two
allocations immediately adjacent. The `-c` parameter tells the search what the
minimum possible distance achievable is. It should be set to 0 for tcmalloc, 8
for avrlibc and 16 for dlmalloc.

```
$ ./runexp.py -j 1 -e 500000 -o /tmp/output -t 3600 -c 8 --starting-state php-emalloc --interaction-sequences sl1024afr98 --allocator avrlibc-r2537 -f 32 -s 32
2018-08-09 15:01:11 INFO     86848 runexp:<module>:75 Testing the avrlibc-r2537 allocator
2018-08-09 15:01:11 INFO     86848 runexp:<module>:101 Utilising PHP's emalloc starting state (571 events)
2018-08-09 15:01:11 INFO     86848 runexp:<module>:163 Running experiment on 1 cores (time limit: 3600, execution limit: 500000, cutoff: 8)

...

2018-08-09 15:01:12 INFO     86848 executor:run_experiment:476 Discovered distances <= the cut off. Shutting down workers ...
2018-08-09 15:01:12 INFO     86848 executor:run_experiment:490 73 successful executions. 0 errors.
2018-08-09 15:01:12 INFO     86848 executor:run_experiment:492 === Progress Report ===
2018-08-09 15:01:12 INFO     86848 executor:run_experiment:495 Time: 0, execs: 1, pos: None, neg: -48
2018-08-09 15:01:12 INFO     86848 executor:run_experiment:495 Time: 0, execs: 4, pos: None, neg: -8
2018-08-09 15:01:12 INFO     86848 executor:run_experiment:495 Time: 0, execs: 5, pos: 248, neg: -8
2018-08-09 15:01:12 INFO     86848 executor:run_experiment:495 Time: 0, execs: 11, pos: 208, neg: -8
2018-08-09 15:01:12 INFO     86848 executor:run_experiment:495 Time: 0, execs: 50, pos: 88, neg: -8
2018-08-09 15:01:12 INFO     86848 executor:run_experiment:495 Time: 0, execs: 66, pos: 48, neg: -8
2018-08-09 15:01:12 INFO     86848 executor:run_experiment:495 Time: 0, execs: 73, pos: 8, neg: -8
2018-08-09 15:01:12 INFO     86848 executor:run_experiment:496 === End Progress Report ===
2018-08-09 15:01:12 INFO     86848 runexp:<module>:170 Min. negative distance: -8
2018-08-09 15:01:12 INFO     86848 runexp:<module>:171 Min. positive distance: 8
```

When the search completes the specified output directly will contain 4 files.

* `pos_trigger.txt` A record of the inputs required to achieve the positive layout
* `neg_trigger.txt` A record of the inputs required to achieve the negative layout
* `result.json` A jsonpickle record of the ExpResult object containing the
configuration settings for the experiment
* `output.log` The log output from the experiment

The triggers cacn be replayed by feeding them directly to the allocator driver.
e.g.

```
$ ./runner/runner-avrlibc-r2537 /tmp/output/neg_trigger.txt
vtx srcptr 665a84
vtx dstptr 665aac
vtx distance -40
```

The printed distance is the address of the first allocation minus the address of
the second allocation. The fact that it is negative means the first allocation
is before the second allocation and it equals the size of the second allocation
(32) plus the metadata overhead (8).

You can generate a log of the heap evolution over time that is consumable by
Thomas Dullien's [heap visualiser](https://github.com/thomasdullien/heap_history_viewer) as follows:

```
$ ./runner/runner-avrlibc-r2537 /tmp/output/neg_trigger.txt 1 2>/tmp/vizlog.json
$ head /tmp/vizlog.json
[{ "type" : "alloc", "tag" : "malloc 32768", "size" : 28, "address" : 6312736 },
{ "type" : "alloc", "tag" : "malloc 32769", "size" : 28, "address" : 6312772 },
{ "type" : "free 32769", "tag" : "realloc_free", "address" : 6312772},
{ "type" : "alloc 32770", "tag" : "realloc_malloc", "size" : 50, "address" : 6312808 },
{ "type" : "free", "tag" : "free 32770", "address" : 6312808},
{ "type" : "alloc", "tag" : "malloc 32771", "size" : 16388, "address" : 6312772 },
{ "type" : "alloc", "tag" : "malloc 32772", "size" : 50, "address" : 6329168 },
{ "type" : "free", "tag" : "free 32772", "address" : 6329168},
{ "type" : "free 0", "tag" : "realloc_free", "address" : 0},
{ "type" : "alloc 32773", "tag" : "realloc_malloc", "size" : 79, "address" : 6329168 },
```

And then, assuming you have `heap_history_viewer` at the same path, generate a visualisation via:

```
$ ~/git/heap_history_viewer/release/HeapVizGL /tmp/vizlog.json
```

Which will result in something similar to the following:

![Heap Visualisation](https://seanhn.files.wordpress.com/2018/08/heap_vis.png)

[1]: https://sean.heelan.io/heaplayout
