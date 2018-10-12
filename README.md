# Introduction

Here you will find the source code related to my paper titled *Automatic Heap
Layout Manipulation for Exploitation*, published at USENIX Security 2018.

The most recent version of the paper can be found in this repository as
`usenix18-heelan.pdf`, and a recording of the presentation and the slides can be
found on the [USENIX website][1].

The `Sieve` subdirectory contains the source code for SIEVE, a framework
for evaluating heap layout manipulation algorithms on synthetic benchmarks.

The `Shrike` subdirectory contains the source code for SHRIKE, a
proof-of-concept template-based exploit generation system, targeting the PHP
language interpreter. SHRIKE allows you to write an exploit containing 'holes'
where heap layout manipulation needs to take place. This partial exploit is then
taken by SHRIKE and completed.  The strength of this approach is that it allows
a human exploit developer to focus on the creative part of the exploit
development process, while letting the machine use its raw reasoning power to
solve the complex but tedious task of heap layout manipulation.

# BibTex

If you wish to cite this work the bibtex is as follows:

```
@inproceedings {HeelanUSENIX2018,
author = {Sean Heelan and Tom Melham and Daniel Kroening},
title = {Automatic Heap Layout Manipulation for Exploitation},
booktitle = {27th {USENIX} Security Symposium ({USENIX} Security 18)},
year = {2018},
isbn = {978-1-931971-46-1},
address = {Baltimore, MD},
pages = {763--779},
url = {https://www.usenix.org/conference/usenixsecurity18/presentation/heelan},
publisher = {{USENIX} Association},
}
```

# Contact

If you have any questions regarding the paper or the code I can be reached via
[sean.heelan@cs.ox.ac.uk](mailto:sean.heelan@cs.ox.ac.uk).

[1]: https://www.usenix.org/conference/usenixsecurity18/presentation/heelan
