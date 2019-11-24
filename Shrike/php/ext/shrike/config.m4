dnl $Id$
dnl config.m4 for extension shrike

dnl Comments in this file start with the string 'dnl'.
dnl Remove where necessary. This file will not work
dnl without editing.

dnl If your extension references something external, use with:

dnl PHP_ARG_WITH(shrike, for shrike support,
dnl Make sure that the comment is aligned:
dnl [  --with-shrike             Include shrike support])

dnl Otherwise use enable:

PHP_ARG_ENABLE(shrike, whether to enable shrike support,
Make sure that the comment is aligned:
[  --enable-shrike           Enable shrike support])

if test "$PHP_SHRIKE" != "no"; then
  dnl Write more examples of tests here...

  dnl # --with-shrike -> check with-path
  dnl SEARCH_PATH="/usr/local /usr"     # you might want to change this
  dnl SEARCH_FOR="/include/shrike.h"  # you most likely want to change this
  dnl if test -r $PHP_SHRIKE/$SEARCH_FOR; then # path given as parameter
  dnl   SHRIKE_DIR=$PHP_SHRIKE
  dnl else # search default path list
  dnl   AC_MSG_CHECKING([for shrike files in default path])
  dnl   for i in $SEARCH_PATH ; do
  dnl     if test -r $i/$SEARCH_FOR; then
  dnl       SHRIKE_DIR=$i
  dnl       AC_MSG_RESULT(found in $i)
  dnl     fi
  dnl   done
  dnl fi
  dnl
  dnl if test -z "$SHRIKE_DIR"; then
  dnl   AC_MSG_RESULT([not found])
  dnl   AC_MSG_ERROR([Please reinstall the shrike distribution])
  dnl fi

  dnl # --with-shrike -> add include path
  dnl PHP_ADD_INCLUDE($SHRIKE_DIR/include)

  dnl # --with-shrike -> check for lib and symbol presence
  dnl LIBNAME=shrike # you may want to change this
  dnl LIBSYMBOL=shrike # you most likely want to change this 

  dnl PHP_CHECK_LIBRARY($LIBNAME,$LIBSYMBOL,
  dnl [
  dnl   PHP_ADD_LIBRARY_WITH_PATH($LIBNAME, $SHRIKE_DIR/$PHP_LIBDIR, SHRIKE_SHARED_LIBADD)
  AC_DEFINE(HAVE_SHRIKELIB,1,[ ])
  dnl ],[
  dnl   AC_MSG_ERROR([wrong shrike lib version or lib not found])
  dnl ],[
  dnl   -L$SHRIKE_DIR/$PHP_LIBDIR -lm
  dnl ])
  dnl
  dnl PHP_SUBST(SHRIKE_SHARED_LIBADD)

  sources="shrike.c"
  PHP_NEW_EXTENSION(shrike, $sources, $ext_shared,, -DZEND_ENABLE_STATIC_TSRMLS_CACHE=1)
  PHP_INSTALL_HEADERS([ext/shrike/shrike_intern.h])
fi
