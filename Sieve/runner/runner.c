#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <inttypes.h>

#define MAX_LINE_LEN 1024
#define VTX "vtx"
#define ALLOC "alloc"
#define FREE "free"
#define REALLOC "realloc"
#define CALLOC "calloc"
#define SRC "src"
#define DST "dst"
#define GAMESTART "gamestart"

#define MAX_ALLOCS 1024 * 512
void *allocd_ptrs[MAX_ALLOCS];
void *src_ptr, *dst_ptr;

#ifdef COUNTHOLES
size_t count_holes(size_t, size_t*, size_t*);
#endif

/* Warning: No function calls that may allocate buffers of differing sizes
 * depending on whether they are launched from Python versus from the command
 * line should take place prior to the main loop below, or during it. An example
 * of such a function is printf, which may trigger the allocation of buffers
 * that will differ in size depending on how it is launched.
*/
int main(int argc, char *argv[])
{
    FILE *fd = NULL;
    int64_t distance = 0;
    char line[MAX_LINE_LEN];
    int first_log = 1;
    int log_json = 0;
#ifdef COUNTHOLES
    size_t src_hole_count, src_hole_space, dst_hole_count, dst_hole_space;
#endif

    if (argc != 2 && argc != 3) {
        fprintf(stderr, "Usage: %s input.txt [1]\n", argv[0]);
        fprintf(stderr,
                "If the third argument is 1 then a JSON log is created\n");
        return 1;
    }

    if (argc == 3 && !strcmp(argv[2], "1")) {
        log_json = 1;
    }

    fd = fopen(argv[1], "r");
    if (fd == NULL) {
        perror("Error");
        return 1;
    }

    while (fgets(line, MAX_LINE_LEN, fd)) {
        char *tok = NULL;
        line[strcspn(line, "\n")] = 0;
        if (!strlen(line)) {
            continue;
        }
        tok = strtok(line, " ");

        if (strcmp(tok, VTX)) {
            fprintf(stderr, "Invalid start of line from %s: %s\n", argv[1],
                    line);
            exit(1);
        }

        tok = strtok(NULL, " ");
        if (!strcmp(tok, ALLOC)) {
            // Format: vtx alloc ID SIZE
            void *allocd_ptr = NULL;
            size_t id, size;
            char *endptr = NULL;
            char *id_str = strtok(NULL, " ");
            char *size_str = strtok(NULL, " ");

            if (!id_str || !size_str) {
                fprintf(stderr, "Invalid alloc ID or size\n");
                exit(1);
            }

            id = strtoll(id_str, &endptr, 10);
            if (*endptr) {
                fprintf(stderr, "Could not convert ID %s to long\n", id_str);
                exit(1);
            }

            if (id >= MAX_ALLOCS) {
                fprintf(stderr,
                        "Allocation ID (%zu) exceeds max allowed value %d\n",
                        id, MAX_ALLOCS);
                exit(1);
            }

            endptr = NULL;
            size = strtoll(size_str, &endptr, 10);
            if (*endptr) {
                fprintf(stderr, "Could not convert size %s to long\n",
                        size_str);
                exit(1);
            }

            allocd_ptr = malloc(size);
            if (!allocd_ptr) {
                fprintf(stderr, "Alloc of size %zu failed\n", size);
                exit(1);
            }

            if (allocd_ptrs[id]) {
                fprintf(stderr, "Duplicate ID %zu\n", id);
                exit(1);
            }

            allocd_ptrs[id] = allocd_ptr;
            if (log_json) {
                if (first_log) {
                    first_log = 0;
                    fprintf(stderr, "[");
                } else {
                    fprintf(stderr, ",\n");
                }
                fprintf(stderr, "{ \"type\" : \"alloc\", "
                        "\"tag\" : \"malloc %zu\", \"size\" : %zu, "
                        "\"address\" : %" PRIuPTR " }", id, size,
                        (uintptr_t) allocd_ptr);
            }
        } else if (!strcmp(tok, CALLOC)) {
            // Format: vtx calloc ID NMEMB SIZE
            void *allocd_ptr = NULL;
            size_t id, nmemb, size;
            char *endptr = NULL;
            char *id_str = strtok(NULL, " ");
            char *nmemb_str = strtok(NULL, " ");
            char *size_str = strtok(NULL, " ");

            if (!id_str || !nmemb_str || !size_str) {
                fprintf(stderr, "Invalid calloc ID, nmemb or size\n");
                exit(1);
            }

            id = strtoll(id_str, &endptr, 10);
            if (*endptr) {
                fprintf(stderr, "Could not convert ID %s to long\n", id_str);
                exit(1);
            }

            if (id >= MAX_ALLOCS) {
                fprintf(stderr,
                        "Allocation ID (%zu) exceeds max allowed value %d\n",
                        id, MAX_ALLOCS);
                exit(1);
            }

            endptr = NULL;
            nmemb = strtoll(nmemb_str, &endptr, 10);
            if (*endptr) {
                fprintf(stderr, "Could not convert nmemb %s to long\n",
                        nmemb_str);
                exit(1);
            }

            endptr = NULL;
            size = strtoll(size_str, &endptr, 10);
            if (*endptr) {
                fprintf(stderr, "Could not convert size %s to long\n",
                        size_str);
                exit(1);
            }

            allocd_ptr = calloc(nmemb, size);
            if (!allocd_ptr) {
                fprintf(stderr, "Calloc of nmemb %zu, size %zu failed\n",
                        nmemb, size);
                exit(1);
            }

            if (allocd_ptrs[id]) {
                fprintf(stderr, "Duplicate ID %zu\n", id);
                exit(1);
            }

            allocd_ptrs[id] = allocd_ptr;
            if (log_json) {
                if (first_log) {
                    first_log = 0;
                    fprintf(stderr, "[");
                } else {
                    fprintf(stderr, ",\n");
                }
                fprintf(stderr, "{ \"type\" : \"alloc\", "
                        "\"tag\" : \"calloc %zu\", \"size\" : %zu, "
                        "\"address\" : %" PRIuPTR " }", id, size * nmemb,
                        (uintptr_t) allocd_ptr);
            }
        } else if (!strcmp(tok, FREE)) {
            // Format: vtx free ID
            size_t id, size;
            char *endptr = NULL;
            char *id_str = strtok(NULL, " ");

            if (!id_str) {
                fprintf(stderr, "Invalid free ID from %s: %s\n",
                        argv[1], line);
                exit(1);
            }

            id = strtoll(id_str, &endptr, 10);
            if (*endptr) {
                fprintf(stderr, "Could not convert ID %s to long\n", id_str);
                exit(1);
            }

            if (id >= MAX_ALLOCS) {
                fprintf(stderr,
                        "Free ID (%zu) exceeds max allowed value %d\n",
                        id, MAX_ALLOCS);
                exit(1);
            }

            if (!allocd_ptrs[id]) {
                fprintf(stderr,
                        "Free ID %zu has not been used for an allocation\n",
                        id);
                exit(1);
            }

            free(allocd_ptrs[id]);
            if (log_json) {
                fprintf(stderr, ",\n{ \"type\" : \"free\", "
                        "\"tag\" : \"free %zu\", \"address\" : %" PRIuPTR "}",
                        id, (uintptr_t) allocd_ptrs[id]);
            }
            allocd_ptrs[id] = NULL;
        } else if (!strcmp(tok, REALLOC)) {
            // Format: vtx realloc OLDID NEWID SIZE
            void *old_ptr, *allocd_ptr;
            size_t old_id, new_id, size;
            char *endptr = NULL;
            char *old_id_str = strtok(NULL, " ");
            char *new_id_str = strtok(NULL, " ");
            char *size_str = strtok(NULL, " ");

            if (!old_id_str || !new_id_str || !size_str) {
                fprintf(stderr, "Invalid realloc IDs or size\n");
                exit(1);
            }

            old_id = strtoll(old_id_str, &endptr, 10);
            if (*endptr) {
                fprintf(stderr, "Could not convert old ID %s to long\n",
                        old_id_str);
                exit(1);
            }

            if (old_id >= MAX_ALLOCS) {
                fprintf(stderr,
                        "Old allocation ID (%zu) exceeds max allowed %d\n",
                        new_id, MAX_ALLOCS);
                exit(1);
            }

            new_id = strtoll(new_id_str, &endptr, 10);
            if (*endptr) {
                fprintf(stderr, "Could not convert new ID %s to long\n",
                        new_id_str);
                exit(1);
            }

            if (new_id >= MAX_ALLOCS) {
                fprintf(stderr,
                        "New allocation ID (%zu) exceeds max allowed %d\n",
                        new_id, MAX_ALLOCS);
                exit(1);
            }

            endptr = NULL;
            size = strtoll(size_str, &endptr, 10);
            if (*endptr) {
                fprintf(stderr, "Could not convert size %s to long\n",
                        size_str);
                exit(1);
            }

            old_ptr = NULL;
            if (old_id) {
                if (!allocd_ptrs[old_id]) {
                    fprintf(stderr,
                            "Realloc ID %zu has not been used for an "
                            "allocation\n", old_id);
                    exit(1);
                }
                old_ptr = allocd_ptrs[old_id];
                allocd_ptrs[old_id] = NULL;
            }

            allocd_ptr = realloc(old_ptr, size);
            if (!allocd_ptr) {
                fprintf(stderr, "Realloc of size %zu failed\n", size);
                exit(1);
            }

            if (allocd_ptrs[new_id]) {
                fprintf(stderr, "Duplicate ID %zu\n", new_id);
                exit(1);
            }

            allocd_ptrs[new_id] = allocd_ptr;
            if (log_json) {
                if (first_log) {
                    first_log = 0;
                    fprintf(stderr, "[");
                } else {
                    fprintf(stderr, ",\n");
                }

                fprintf(stderr, "{ \"type\" : \"free %zu\", "
                        "\"tag\" : \"realloc_free\", "
                        "\"address\" : %" PRIuPTR "},\n",
                        old_id, (uintptr_t) old_ptr);
                fprintf(stderr, "{ \"type\" : \"alloc %zu\", "
                        "\"tag\" : \"realloc_malloc\", "
                        "\"size\" : %zu, \"address\" : %" PRIuPTR " }",
                        new_id, size, (uintptr_t) allocd_ptr);
            }
        } else if (!strcmp(tok, SRC)) {
            // Format: vtx src SIZE
            size_t size;
            char *endptr = NULL;
            char *size_str;

            if (src_ptr) {
                fprintf(stderr, "Multiple attempts to allocate src pointer\n");
                exit(1);
            }

            size_str = strtok(NULL, " ");

            if (!size_str) {
                fprintf(stderr, "Invalid src size from %s: %s\n", argv[1],
                        line);
                exit(1);
            }

            size = strtoll(size_str, &endptr, 10);
            if (*endptr) {
                fprintf(stderr, "Could not convert src size %s to long\n",
                        size_str);
                exit(1);
            }

#ifdef COUNTHOLES
            count_holes(size, &src_hole_count, &src_hole_space);
#endif
            src_ptr = malloc(size);
            if (!src_ptr) {
                fprintf(stderr, "Src alloc of size %zu failed\n", size);
                exit(1);
            }
            if (log_json) {
                if (first_log) {
                    first_log = 0;
                    fprintf(stderr, "[");
                } else {
                    fprintf(stderr, ",\n");
                }
                fprintf(stderr, "{ \"type\" : \"alloc\", \"tag\" : \"src\", "
                        "\"size\" : %zu, \"address\" : %" PRIuPTR " },\n",
                        size, (uintptr_t) src_ptr);
                fprintf(stderr,
                        "{ \"type\" : \"event\", \"tag\" : \"src\" }");
            }
        } else if (!strcmp(tok, DST)) {
            // Format: vtx dst SIZE
            size_t size;
            char *endptr = NULL;
            char *size_str;

            if (dst_ptr) {
                fprintf(stderr, "Multiple attempts to allocate dst pointer\n");
                exit(1);
            }

            size_str = strtok(NULL, " ");

            if (!size_str) {
                fprintf(stderr, "Invalid dst size from %s: %s\n", argv[1],
                        line);
                exit(1);
            }

            size = strtoll(size_str, &endptr, 10);
            if (*endptr) {
                fprintf(stderr, "Could not convert dst size %s to long\n",
                        size_str);
                exit(1);
            }

#ifdef COUNTHOLES
            count_holes(size, &dst_hole_count, &dst_hole_space);
#endif
            dst_ptr = malloc(size);
            if (!dst_ptr) {
                fprintf(stderr, "Dst alloc of size %zu failed\n", size);
                exit(1);
            }
            if (log_json) {
                if (first_log) {
                    first_log = 0;
                    fprintf(stderr, "[");
                } else {
                    fprintf(stderr, ",\n");
                }
                fprintf(stderr, "{ \"type\" : \"alloc\", \"tag\" : \"dst\", "
                        "\"size\" : %zu, \"address\" : %" PRIuPTR " },\n",
                        size, (uintptr_t) dst_ptr);
                fprintf(stderr,
                        "{ \"type\" : \"event\", \"tag\" : \"dst\" }");
            }
        } else if (!strcmp(tok, GAMESTART)){
            if (log_json) {
                if (first_log) {
                    first_log = 0;
                    fprintf(stderr, "[");
                } else {
                    fprintf(stderr, ",\n");
                }
                fprintf(stderr,
                        "{ \"type\" : \"event\", \"tag\" : \"gamestart\" }");
            }
        } else {
            fprintf(stderr, "Invalid directive in %s: %s\n", argv[1], line);
            exit(1);
        }
    }
    if (log_json) {
        fprintf(stderr, "]\n");
    }

    if (!src_ptr) {
        fprintf(stderr, "Missing a source allocation directive in %s\n",
                argv[1]);
        exit(1);
    } else if (!dst_ptr) {
        fprintf(stderr, "Missing a destination allocation directive in %s\n",
                argv[1]);
        exit(1);
    }

#ifdef COUNTHOLES
    printf("Holes for src size: %zu, space: %zu\n", src_hole_count,
            src_hole_space);
    printf("Holes for dst size: %zu, space: %zu\n", dst_hole_count,
            dst_hole_space);
#endif

    printf("vtx srcptr %" PRIxPTR "\n", src_ptr);
    printf("vtx dstptr %" PRIxPTR "\n", dst_ptr);
    distance = (uint64_t) src_ptr - (uint64_t) dst_ptr;
    printf("vtx distance %" PRId64 "\n", distance);

    fclose(fd);
    return 0;
}
