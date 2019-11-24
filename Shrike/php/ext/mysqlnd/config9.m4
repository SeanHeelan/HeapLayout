dnl
dnl $Id$
dnl config.m4 for mysqlnd driver

PHP_ARG_ENABLE(mysqlnd, whether to enable mysqlnd,
  [  --enable-mysqlnd        Enable mysqlnd explicitly, will be done implicitly
                          when required by other extensions], no, yes)

PHP_ARG_ENABLE(mysqlnd_compression_support, whether to disable compressed protocol support in mysqlnd,
[  --disable-mysqlnd-compression-support
                          Disable support for the MySQL compressed protocol in mysqlnd], yes, no)

if test -z "$PHP_ZLIB_DIR"; then
  PHP_ARG_WITH(zlib-dir, for the location of libz,
  [  --with-zlib-dir[=DIR]     mysqlnd: Set the path to libz install prefix], no, no)
fi

dnl If some extension uses mysqlnd it will get compiled in PHP core
if test "$PHP_MYSQLND" != "no" || test "$PHP_MYSQLND_ENABLED" = "yes"; then
  mysqlnd_ps_sources="mysqlnd_ps.c mysqlnd_ps_codec.c"
  mysqlnd_base_sources="mysqlnd_connection.c mysqlnd_alloc.c mysqlnd_charset.c mysqlnd_wireprotocol.c \
                   mysqlnd_loaddata.c mysqlnd_reverse_api.c mysqlnd_vio.c mysqlnd_protocol_frame_codec.c \
                   mysqlnd_statistics.c mysqlnd_driver.c mysqlnd_ext_plugin.c mysqlnd_auth.c \
				   mysqlnd_result.c mysqlnd_result_meta.c mysqlnd_debug.c mysqlnd_commands.c \
				   mysqlnd_block_alloc.c mysqlnd_read_buffer.c mysqlnd_plugin.c php_mysqlnd.c"


  if test "$PHP_MYSQLND_COMPRESSION_SUPPORT" != "no"; then
    AC_DEFINE([MYSQLND_COMPRESSION_WANTED], 1, [Enable compressed protocol support])
  fi

  AC_DEFINE([MYSQLND_SSL_SUPPORTED], 1, [Enable core mysqlnd SSL code])

  test -z "$PHP_OPENSSL" && PHP_OPENSSL=no

  if test "$PHP_OPENSSL" != "no" || test "$PHP_OPENSSL_DIR" != "no"; then
    AC_CHECK_LIB(ssl, DSA_get_default_method, AC_DEFINE(HAVE_DSA_DEFAULT_METHOD, 1, [OpenSSL 0.9.7 or later]))
    AC_CHECK_LIB(crypto, X509_free, AC_DEFINE(HAVE_DSA_DEFAULT_METHOD, 1, [OpenSSL 0.9.7 or later]))

    PHP_SETUP_OPENSSL(MYSQLND_SHARED_LIBADD, [AC_DEFINE(MYSQLND_HAVE_SSL,1,[Enable mysqlnd code that uses OpenSSL directly])])
  fi

  mysqlnd_sources="$mysqlnd_base_sources $mysqlnd_ps_sources"
  PHP_NEW_EXTENSION(mysqlnd, $mysqlnd_sources, $ext_shared,, -DZEND_ENABLE_STATIC_TSRMLS_CACHE=1)
  PHP_ADD_BUILD_DIR([ext/mysqlnd], 1)
  PHP_INSTALL_HEADERS([ext/mysqlnd/])
fi

if test "$PHP_MYSQLND" != "no" || test "$PHP_MYSQLND_ENABLED" = "yes" || test "$PHP_MYSQLI" != "no"; then
  PHP_ADD_BUILD_DIR([ext/mysqlnd], 1)
fi
