dnl $Id$
dnl config.m4 for extension dve

dnl Comments in this file start with the string 'dnl'.
dnl Remove where necessary. This file will not work
dnl without editing.

dnl If your extension references something external, use with:

dnl PHP_ARG_WITH(dve, for dve support,
dnl Make sure that the comment is aligned:
dnl [  --with-dve             Include dve support])

dnl Otherwise use enable:

PHP_ARG_ENABLE(dve, whether to enable dve support,
Make sure that the comment is aligned:
[  --enable-dve           Enable dve support])

if test "$PHP_DVE" != "no"; then
  dnl Write more examples of tests here...

  dnl # --with-dve -> check with-path
  dnl SEARCH_PATH="/usr/local /usr"     # you might want to change this
  dnl SEARCH_FOR="/include/dve.h"  # you most likely want to change this
  dnl if test -r $PHP_DVE/$SEARCH_FOR; then # path given as parameter
  dnl   DVE_DIR=$PHP_DVE
  dnl else # search default path list
  dnl   AC_MSG_CHECKING([for dve files in default path])
  dnl   for i in $SEARCH_PATH ; do
  dnl     if test -r $i/$SEARCH_FOR; then
  dnl       DVE_DIR=$i
  dnl       AC_MSG_RESULT(found in $i)
  dnl     fi
  dnl   done
  dnl fi
  dnl
  dnl if test -z "$DVE_DIR"; then
  dnl   AC_MSG_RESULT([not found])
  dnl   AC_MSG_ERROR([Please reinstall the dve distribution])
  dnl fi

  dnl # --with-dve -> add include path
  dnl PHP_ADD_INCLUDE($DVE_DIR/include)

  dnl # --with-dve -> check for lib and symbol presence
  dnl LIBNAME=dve # you may want to change this
  dnl LIBSYMBOL=dve # you most likely want to change this 

  dnl PHP_CHECK_LIBRARY($LIBNAME,$LIBSYMBOL,
  dnl [
  dnl   PHP_ADD_LIBRARY_WITH_PATH($LIBNAME, $DVE_DIR/$PHP_LIBDIR, DVE_SHARED_LIBADD)
  dnl   AC_DEFINE(HAVE_DVELIB,1,[ ])
  dnl ],[
  dnl   AC_MSG_ERROR([wrong dve lib version or lib not found])
  dnl ],[
  dnl   -L$DVE_DIR/$PHP_LIBDIR -lm
  dnl ])
  dnl
  dnl PHP_SUBST(DVE_SHARED_LIBADD)

  PHP_NEW_EXTENSION(dve, dve.c, $ext_shared,, -DZEND_ENABLE_STATIC_TSRMLS_CACHE=1)
fi
