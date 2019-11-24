/*
  +----------------------------------------------------------------------+
  | PHP Version 7                                                        |
  +----------------------------------------------------------------------+
  | Copyright (c) 1997-2017 The PHP Group                                |
  +----------------------------------------------------------------------+
  | This source file is subject to version 3.01 of the PHP license,      |
  | that is bundled with this package in the file LICENSE, and is        |
  | available through the world-wide-web at the following url:           |
  | http://www.php.net/license/3_01.txt                                  |
  | If you did not receive a copy of the PHP license and are unable to   |
  | obtain it through the world-wide-web, please send a note to          |
  | license@php.net so we can mail you a copy immediately.               |
  +----------------------------------------------------------------------+
  | Author: Sean Heelan (sean@vertex)									 |
  +----------------------------------------------------------------------+
*/

/* $Id$ */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include "php.h"
#include "php_ini.h"
#include "ext/standard/info.h"
#include "php_shrike.h"
#include "shrike_intern.h"

// The maximum number of allocations that can be requested to be recorded via
// the shrike_record_alloc function from PHP
#define SHRIKE_MAX_RECORDED_ALLOCS 64
// The maximum number of pointers that can be recorded when pointer recording is
// enabled via shrike_pointer_sequence_st
#define SHRIKE_MAX_RECORDED_POINTERS 8192

/* True global resources - no need for thread safety here */
static int le_shrike;

// I think this should be fine as we're not going to be running multiple
// instances of PHP. Docs on that are here
// https://secure.php.net/manual/en/internals2.structure.globals.php

// Indicates whether or not malloc/free/calloc/realloc calls should be logged
int shrike_logging_enabled;
// Indicates whether or not to enable searching for pointers in memory
int shrike_pointer_logging_enabled;

void *shrike_allocated_pointers[SHRIKE_MAX_RECORDED_POINTERS];
size_t shrike_allocated_sizes[SHRIKE_MAX_RECORDED_POINTERS];
size_t shrike_allocated_pointers_idx;

int shrike_alloc_recording_enabled;

void* shrike_recorded_allocs[SHRIKE_MAX_RECORDED_ALLOCS];
size_t shrike_current_index;
size_t shrike_alloc_index;
size_t shrike_alloc_id_to_use;
size_t shrike_expected_alloc_size;

/* {{{ shrike_pointer_sequence_start
 */
PHP_FUNCTION(shrike_pointer_sequence_start)
{
	shrike_pointer_logging_enabled = 1;
}
/* }}} */

/* {{{ log_proc_map
 */
int log_proc_map()
{
	size_t read;
	size_t len;
	char *line = NULL;

	int tmp_logging = shrike_logging_enabled;
	int tmp_pointer_logging = shrike_pointer_logging_enabled;
	shrike_logging_enabled = 0;
	shrike_pointer_logging_enabled = 0;

	FILE *fp = fopen("/proc/self/maps", "r");
	if (!fp) {
		shrike_logging_enabled = tmp_logging;
		shrike_pointer_logging_enabled = tmp_pointer_logging;
		return 1;
	}

	while ((read = getline(&line, &len, fp)) != -1) {
		printf("vtx map %s", line);
	}

	fclose(fp);
	if (line) {
		free(line);
	}

	shrike_logging_enabled = tmp_logging;
	shrike_pointer_logging_enabled = tmp_pointer_logging;
	return 0;
}
/* }}} */

/* {{{ shrike_pointer_sequence_end
 */
PHP_FUNCTION(shrike_pointer_sequence_end)
{
	size_t i = 0;

	if (!shrike_pointer_logging_enabled) {
		php_error(E_ERROR, "Pointer logging has not been enabled");
		return;
	}

	if (log_proc_map()) {
		php_error(E_ERROR, "Failed to log /proc/self/maps");
		return;
	}

	for (i = 0; i < shrike_allocated_pointers_idx; ++i) {
		size_t *buf = shrike_allocated_pointers[i];
		size_t size = shrike_allocated_sizes[i];

		if (buf && size >= 8) {
			size_t j = 0;
			for (j = 0; j < size / 8; ++j) {
				size_t content = buf[j];
				// The driver script will check each candidate pointer against
				// the logged process map, but the following check weeds out a
				// lot of data which is obviously not a pointer.
				if (content && content < 0x7fffffffffff && !(content & 0xf)) {
					printf("vtx ptr %lu %lu 0x%" PRIxPTR " 0x%" PRIxPTR "\n",
							size, j * 8, (uintptr_t) buf, (uintptr_t) content);
				}
			}
		}
	}

	shrike_pointer_logging_enabled = 0;
	shrike_allocated_pointers_idx = 0;
	memset(shrike_allocated_pointers, 0x0,
			SHRIKE_MAX_RECORDED_POINTERS * sizeof(void *));
}
/* }}} */

/* {{{ shrike_sequence_start
 */
PHP_FUNCTION(shrike_sequence_start)
{
	shrike_logging_enabled = 1;
}
/* }}} */

/* {{{ shrike_sequence_end
 */
PHP_FUNCTION(shrike_sequence_end)
{
	shrike_logging_enabled = 0;
}
/* }}} */

/* {{{ shrike_record_alloc
 */
ZEND_BEGIN_ARG_INFO_EX(arginfo_shrike_record_alloc, 0, 0, 2)
	ZEND_ARG_INFO(0, index)
	ZEND_ARG_INFO(0, alloc_id)
ZEND_END_ARG_INFO()

PHP_FUNCTION(shrike_record_alloc)
{
	size_t index, alloc_id, expected_size;

	if (zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "lll",
				&index, &alloc_id, &expected_size) == FAILURE) {
	    return;
	}

	if (!intern_shrike_record_alloc(index, alloc_id, expected_size)) {
		php_error(E_ERROR, "shrike_record_alloc failed");
		RETURN_FALSE;
	}
}
/* }}} */

/* {{{ intern_shrike_record_alloc
 */
int intern_shrike_record_alloc(
        size_t index, size_t alloc_id, size_t expected_size)
{
	if (shrike_recorded_allocs[alloc_id]) {
		php_error(E_ERROR, "Attempting to reuse an inuse allocation ID");
		return 0;
	}

	shrike_alloc_recording_enabled = 1;
	shrike_current_index = 0;
	shrike_alloc_index = index;
	shrike_alloc_id_to_use = alloc_id;
	shrike_expected_alloc_size = expected_size;
}
/* }}} */

/* {{{ get_distance
 */
long get_distance(size_t id0, size_t id1)
{
	void *alloc0, *alloc1;

	if (id0 > SHRIKE_MAX_RECORDED_ALLOCS || id1 > SHRIKE_MAX_RECORDED_ALLOCS) {
		php_error(E_ERROR, "Requested allocation ID is too large");
		return 0;
	}

	alloc0 = shrike_recorded_allocs[id0];
	if (!alloc0) {
		php_error(E_ERROR, "Invalid first ID");
		return 0;
	}

	alloc1 = shrike_recorded_allocs[id1];
	if (!alloc1) {
		php_error(E_ERROR, "Invalid second ID");
		return 0;
	}

	return (size_t) alloc0 - (size_t) alloc1;
}
/* }}} */

/* {{{ shrike_print_distance
 */
ZEND_BEGIN_ARG_INFO_EX(arginfo_shrike_print_distance, 0, 0, 2)
	ZEND_ARG_INFO(0, id0)
	ZEND_ARG_INFO(0, id1)
ZEND_END_ARG_INFO()

PHP_FUNCTION(shrike_print_distance)
{
	size_t id0, id1, distance;

	if (zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "ll",
				&id0, &id1) == FAILURE) {
	    return;
	}
	distance = get_distance(id0, id1);
	printf("vtx distance %" PRId64 "\n", distance);
	fflush(stdout);
	RETURN_LONG(distance);
}
/* }}} */

/* {{{ shrike_get_distance
 */
ZEND_BEGIN_ARG_INFO_EX(arginfo_shrike_get_distance, 0, 0, 2)
	ZEND_ARG_INFO(0, id0)
	ZEND_ARG_INFO(0, id1)
ZEND_END_ARG_INFO()

PHP_FUNCTION(shrike_get_distance)
{
	size_t id0, id1, distance;

	if (zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "ll",
				&id0, &id1) == FAILURE) {
	    return;
	}

	RETURN_LONG(get_distance(id0, id1));
}
/* }}} */

/* {{{ PHP_MINIT_FUNCTION
 */
PHP_MINIT_FUNCTION(shrike)
{
	/* If you have INI entries, uncomment these lines
	REGISTER_INI_ENTRIES();
	*/
	return SUCCESS;
}
/* }}} */

/* {{{ PHP_MSHUTDOWN_FUNCTION
 */
PHP_MSHUTDOWN_FUNCTION(shrike)
{
	return SUCCESS;
}
/* }}} */

/* {{{ PHP_MINFO_FUNCTION
 */
PHP_MINFO_FUNCTION(shrike)
{
	php_info_print_table_start();
	php_info_print_table_header(2, "shrike support", "enabled");
	php_info_print_table_end();

	/* Remove comments if you have entries in php.ini
	DISPLAY_INI_ENTRIES();
	*/
}
/* }}} */

/* {{{ shrike_functions[]
 *
 * Every user visible function must have an entry in shrike_functions[].
 */
const zend_function_entry shrike_functions[] = {
	PHP_FE(shrike_sequence_start, NULL)
	PHP_FE(shrike_sequence_end, NULL)
	PHP_FE(shrike_pointer_sequence_start, NULL)
	PHP_FE(shrike_pointer_sequence_end, NULL)
	PHP_FE(shrike_record_alloc, arginfo_shrike_record_alloc)
	PHP_FE(shrike_print_distance, arginfo_shrike_print_distance)
	PHP_FE(shrike_get_distance, arginfo_shrike_get_distance)
	PHP_FE_END	/* Must be the last line in shrike_functions[] */
};
/* }}} */

/* {{{ shrike_module_entry
 */
zend_module_entry shrike_module_entry = {
	STANDARD_MODULE_HEADER,
	"shrike",
	shrike_functions,
	PHP_MINIT(shrike),
	PHP_MSHUTDOWN(shrike),
	NULL,
	NULL,
	PHP_MINFO(shrike),
	PHP_SHRIKE_VERSION,
	STANDARD_MODULE_PROPERTIES
};
/* }}} */

#ifdef COMPILE_DL_SHRIKE
#ifdef ZTS
ZEND_TSRMLS_CACHE_DEFINE()
#endif
ZEND_GET_MODULE(shrike)
#endif

/*
 * Local variables:
 * tab-width: 4
 * c-basic-offset: 4
 * End:
 * vim600: noet sw=4 ts=4 fdm=marker
 * vim<600: noet sw=4 ts=4
 */
