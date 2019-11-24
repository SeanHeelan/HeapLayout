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
  | Author: Sean Heelan (sean@vertex.re)                                 |
  +----------------------------------------------------------------------+
*/

/* $Id$ */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <sys/mman.h>

#include "php.h"
#include "php_ini.h"
#include "ext/standard/info.h"
#include "php_dve.h"

#define MAX_DVE_BUFFERS 8192

/* True global resources - no need for thread safety here */
static int le_dve;

uint8_t *buffers[MAX_DVE_BUFFERS];
size_t next_buffer_idx;

/* {{{ dve_alloc_buffer
 * Allocate and zero out a new buffer of the requested size. The returned ID can
 * be used to refer to the allocated buffer in future operations, such as
 * reading, writing and deallocation.
 */
ZEND_BEGIN_ARG_INFO_EX(arginfo_dve_alloc_buffer, 0, 0, 1)
	ZEND_ARG_INFO(0, size)
ZEND_END_ARG_INFO()

PHP_FUNCTION(dve_alloc_buffer)
{
	size_t sz;
	uint8_t *ptr = NULL;

	if (zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "l", &sz) == FAILURE) {
	    return;
	}

	if (next_buffer_idx >= MAX_DVE_BUFFERS) {
		php_error(E_ERROR, "Maximum number of allocated buffers exceeded");
		RETURN_FALSE;
	}

	ptr = emalloc(sz);
	if (!ptr) {
		php_error(E_ERROR, "Failed to allocate buffer");
		RETURN_FALSE;
	}
	memset(ptr, 0, sz);

	buffers[next_buffer_idx] = ptr;
	RETURN_LONG(next_buffer_idx++);
}
/* }}} */

/* {{{ dve_mmap_executable_buffer
 * mmap an executable buffer. The returned ID can be used to refer to the
 * allocated buffer in future operations, such as reading, writing and
 * deallocation.
 */
ZEND_BEGIN_ARG_INFO_EX(arginfo_dve_mmap_executable_buffer, 0, 0, 1)
	ZEND_ARG_INFO(0, size)
ZEND_END_ARG_INFO()

PHP_FUNCTION(dve_mmap_executable_buffer)
{
	size_t sz;
	uint8_t *ptr = NULL;

	if (zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "l", &sz) == FAILURE) {
	    return;
	}

	if (next_buffer_idx >= MAX_DVE_BUFFERS) {
		php_error(E_ERROR, "Maximum number of allocated buffers exceeded");
		RETURN_FALSE;
	}

	ptr = mmap(NULL, sz, PROT_EXEC | PROT_READ | PROT_WRITE,
			MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
	if (!ptr) {
		php_error(E_ERROR, "Failed to allocate buffer");
		RETURN_FALSE;
	}
	memset(ptr, 0, sz);

	buffers[next_buffer_idx] = ptr;
	RETURN_LONG(next_buffer_idx++);
}
/* }}} */

/* {{{ dve_free_buffer
 */
ZEND_BEGIN_ARG_INFO_EX(arginfo_dve_free_buffer, 0, 0, 1)
	ZEND_ARG_INFO(0, buf)
ZEND_END_ARG_INFO()

PHP_FUNCTION(dve_free_buffer)
{
	size_t buf_id;

	if (zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "l",
				&buf_id) == FAILURE) {
	    return;
	}

	if (!buffers[buf_id]) {
		php_error(E_ERROR, "Attempting to free already free buffer");
		RETURN_FALSE;
	}

	efree(buffers[buf_id]);
	buffers[buf_id] = NULL;
}
/* }}} */

/* {{{ dve_write_to_buffer
 */
ZEND_BEGIN_ARG_INFO_EX(arginfo_dve_write_to_buffer, 0, 0, 3)
	ZEND_ARG_INFO(0, dst)
	ZEND_ARG_INFO(0, src)
	ZEND_ARG_INFO(0, count)
ZEND_END_ARG_INFO()

PHP_FUNCTION(dve_write_to_buffer)
{
	uint8_t *dst;
	char *src;
	size_t src_len, buf_id;

	if (zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "ls",
				&buf_id, &src, &src_len) == FAILURE) {
	    return;
	}

	dst = buffers[buf_id];
	if (!dst) {
		php_error(E_ERROR, "Attempting to write to free buffer");
		RETURN_FALSE;
	}

	// Don't copy the trailing NULL
	memcpy(dst, src, src_len);
}
/* }}} */

/* {{{ dve_store_buffer_address
 * Store the address of the buffer referenced by the third argument at the
 * specified offset in the buffer referenced by the first argument. This is
 * intended to simulate situations in which the address of a function pointer
 * table, for example, is stored in another object in order to be leaked or
 * corrupted.
 */
ZEND_BEGIN_ARG_INFO_EX(arginfo_dve_store_buffer_to_address, 0, 0, 3)
	ZEND_ARG_INFO(0, dst)
	ZEND_ARG_INFO(0, offset)
	ZEND_ARG_INFO(0, src)
ZEND_END_ARG_INFO()

PHP_FUNCTION(dve_store_buffer_address)
{
	size_t idx;
	size_t dst_buf_id, src_buf_id, offset;
	uint8_t *dst, *src;

	if (zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "lll",
				&dst_buf_id, &offset, &src_buf_id) == FAILURE) {
	    return;
	}

	dst = buffers[dst_buf_id];
	if (!dst) {
		php_error(E_ERROR, "Attempting to write to free buffer");
		RETURN_FALSE;
	}

	src = buffers[src_buf_id];
	if (!dst) {
		php_error(E_ERROR, "Attempting to reference a free buffer");
		RETURN_FALSE;
	}

	for (idx = 0; idx < sizeof(uint8_t*); ++idx) {
		dst[offset + idx] = ((size_t) src >> (idx * 8)) & 0xff;
	}
}
/* }}} */

/* {{{ dve_address_of_buffer
 * Retrieve the address of the specified buffer
 */
ZEND_BEGIN_ARG_INFO_EX(arginfo_dve_address_of_buffer, 0, 0, 1)
	ZEND_ARG_INFO(0, buf)
ZEND_END_ARG_INFO()

PHP_FUNCTION(dve_address_of_buffer)
{
	size_t buf_id;
	uint8_t *buf;

	if (zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "l",
				&buf_id) == FAILURE) {
	    return;
	}

	buf = buffers[buf_id];
	if (!buf) {
		php_error(E_ERROR, "Buffer already freed");
		RETURN_FALSE;
	}

	RETURN_LONG((size_t) buf);
}
/* }}} */

/* {{{ dve_read_from_buffer
 */
ZEND_BEGIN_ARG_INFO_EX(arginfo_dve_read_from_buffer, 0, 0, 3)
	ZEND_ARG_INFO(0, src)
	ZEND_ARG_INFO(0, start_idx)
	ZEND_ARG_INFO(0, count)
ZEND_END_ARG_INFO()

PHP_FUNCTION(dve_read_from_buffer)
{
	size_t start_idx, count, buf_id;
	uint8_t *src;
	zend_string *content;

	if (zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "lll",
				&buf_id, &start_idx, &count) == FAILURE) {
	    return;
	}

	src = buffers[buf_id];
	if (!src) {
		php_error(E_ERROR, "Attempting to read from free buffer");
		RETURN_FALSE;
	}

	content = zend_string_alloc(count, 0);
	if (!content) {
		php_error(E_ERROR, "Failed to allocate destination buffer");
		RETURN_FALSE;
	}

	memcpy(ZSTR_VAL(content), src + start_idx , count);
	RETURN_STR(content);
}
/* }}} */

/* {{{ dve_call_function_pointer
 */
ZEND_BEGIN_ARG_INFO_EX(arginfo_dve_call_function_pointer, 0, 0, 2)
	ZEND_ARG_INFO(0, src)
	ZEND_ARG_INFO(0, start_idx)
ZEND_END_ARG_INFO()

typedef void (*FunctionPointer)();

PHP_FUNCTION(dve_call_function_pointer)
{
	size_t start_idx, buf_id;
	uint8_t *src;
	zend_string *content;
	FunctionPointer ptr;

	if (zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "ll",
				&buf_id, &start_idx) == FAILURE) {
	    return;
	}

	src = buffers[buf_id];
	if (!src) {
		php_error(E_ERROR, "Attempting to read from free buffer");
		RETURN_FALSE;
	}

	ptr = *((FunctionPointer*) (src + start_idx));
	ptr();
}
/* }}} */

/* {{{ php_dve_destroy_resource
*/
static void php_dve_destroy_resource(zend_resource *rsrc)
{
	efree(rsrc->ptr);
}

/* }}} */

/* {{{ PHP_MINIT_FUNCTION
 */
PHP_MINIT_FUNCTION(dve)
{
	le_dve = zend_register_list_destructors_ex(php_dve_destroy_resource, NULL,
			"dve", module_number);
	return SUCCESS;
}
/* }}} */

/* {{{ PHP_MSHUTDOWN_FUNCTION
 */
PHP_MSHUTDOWN_FUNCTION(dve)
{
	/* uncomment this line if you have INI entries
	UNREGISTER_INI_ENTRIES();
	*/
	return SUCCESS;
}
/* }}} */

/* {{{ PHP_MINFO_FUNCTION
 */
PHP_MINFO_FUNCTION(dve)
{
	php_info_print_table_start();
	php_info_print_table_header(2, "dve support", "enabled");
	php_info_print_table_end();

}
/* }}} */

/* {{{ dve_functions[]
 *
 * Every user visible function must have an entry in dve_functions[].
 */
const zend_function_entry dve_functions[] = {
	PHP_FE(dve_alloc_buffer, arginfo_dve_alloc_buffer)
	PHP_FE(dve_mmap_executable_buffer, arginfo_dve_mmap_executable_buffer)
	PHP_FE(dve_write_to_buffer, arginfo_dve_write_to_buffer)
	PHP_FE(dve_read_from_buffer, arginfo_dve_read_from_buffer)
	PHP_FE(dve_free_buffer, arginfo_dve_free_buffer)
	PHP_FE(dve_store_buffer_address, arginfo_dve_store_buffer_to_address)
	PHP_FE(dve_address_of_buffer, arginfo_dve_address_of_buffer)
	PHP_FE(dve_call_function_pointer, arginfo_dve_call_function_pointer)
	PHP_FE_END	/* Must be the last line in dve_functions[] */
};
/* }}} */

/* {{{ dve_module_entry
 */
zend_module_entry dve_module_entry = {
	STANDARD_MODULE_HEADER,
	"dve",
	dve_functions,
	PHP_MINIT(dve),
	PHP_MSHUTDOWN(dve),
	NULL,
	NULL,
	PHP_MINFO(dve),
	PHP_DVE_VERSION,
	STANDARD_MODULE_PROPERTIES
};
/* }}} */

#ifdef COMPILE_DL_DVE
#ifdef ZTS
ZEND_TSRMLS_CACHE_DEFINE()
#endif
ZEND_GET_MODULE(dve)
#endif

/*
 * Local variables:
 * tab-width: 4
 * c-basic-offset: 4
 * End:
 * vim600: noet sw=4 ts=4 fdm=marker
 * vim<600: noet sw=4 ts=4
 */
