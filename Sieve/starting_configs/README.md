The `transform.py` script expects the provided log to have enties of the
following form:

```
vtx malloc start SIZE
vtx malloc end PTR
vtx realloc start SIZE OLDPTR
vtx realloc end NEWPTR
vtx calloc start NMEMB SIZE
vtx calloc end PTR
vtx free PTR
```

All values are expected to be base 10.

Such a log can be created in gdb by adding breakpoints in the relevant locations
and then just printing the required data e.g. if breakpoint 1 is at the entry
point to malloc then the following will add the required commands:

```
commands 1
printf "vtx malloc start %lu\n", $rdi
c
end
```

`transform.py` consolidates these entries into single-line allocator
interactions of the following form:

```
vtx alloc SIZE 0xPTR
vtx realloc SIZE 0xOLDPTR 0xNEWPTR
vtx calloc NMEMB SIZE 0xPTR
vtx free 0xPTR
```

All pointers are base 16 and all other number values are base 10.
