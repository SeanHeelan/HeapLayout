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

#define MAX_ALLOCS 1024 * 512
void *allocd_ptrs[MAX_ALLOCS];

void count_exclusive_captures(size_t, size_t, size_t*);

void do_hole_count(void) {
    size_t count = 0;
    count_exclusive_captures(8, 8, &count);
    printf("8-8, %d\n", count);
    count_exclusive_captures(8, 64, &count);
    printf("8-64, %d\n", count);
    count_exclusive_captures(8, 512, &count);
    printf("8-512, %d\n", count);
    count_exclusive_captures(8, 4096, &count);
    printf("8-4096, %d\n", count);
    count_exclusive_captures(8, 16384, &count);
    printf("8-16384, %d\n", count);
    count_exclusive_captures(8, 65536, &count);
    printf("8-65536, %d\n", count);

    count_exclusive_captures(64, 64, &count);
    printf("64-64, %d\n", count);
    count_exclusive_captures(64, 512, &count);
    printf("64-512, %d\n", count);
    count_exclusive_captures(64, 4096, &count);
    printf("64-4096, %d\n", count);
    count_exclusive_captures(64, 16384, &count);
    printf("64-16384, %d\n", count);
    count_exclusive_captures(64, 65536, &count);
    printf("64-65536, %d\n", count);

    count_exclusive_captures(512, 512, &count);
    printf("512-512, %d\n", count);
    count_exclusive_captures(512, 4096, &count);
    printf("512-4096, %d\n", count);
    count_exclusive_captures(512, 16384, &count);
    printf("512-16384, %d\n", count);
    count_exclusive_captures(512, 65536, &count);
    printf("512-65536, %d\n", count);

    count_exclusive_captures(4096, 4096, &count);
    printf("4096-4096, %d\n", count);
    count_exclusive_captures(4096, 16384, &count);
    printf("4096-16384, %d\n", count);
    count_exclusive_captures(4096, 65536, &count);
    printf("4096-65536, %d\n", count);

    count_exclusive_captures(16384, 16384, &count);
    printf("16384-16384, %d\n", count);
    count_exclusive_captures(16384, 65536, &count);
    printf("16384-65536, %d\n", count);

    count_exclusive_captures(65536, 65536, &count);
    printf("65536-65536, %d\n", count);
}

int main(int argc, char *argv[])
{
    FILE *fd = NULL;
    char line[MAX_LINE_LEN];

    if (argc != 2) {
        fprintf(stderr, "Usage: %s input.txt \n", argv[0]);
        return 1;
    }

    printf("Processing %s ...\n", argv[1]);
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
        } else {
            fprintf(stderr, "Invalid directive in %s: %s\n", argv[1], line);
            exit(1);
        }
    }

    do_hole_count();
    fclose(fd);
    return 0;
}
