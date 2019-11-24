--TEST--
Testing wrong parameter resource in imageantialias() of GD library
--CREDITS--
Guilherme Blanco <guilhermeblanco [at] hotmail [dot] com>
#testfest PHPSP on 2009-06-20
--SKIPIF--
<?php 
if (!extension_loaded("gd")) die("skip GD not present");
if (!GD_BUNDLED) die("skip requires bundled GD library\n");
?>
--FILE--
<?php
$image = tmpfile();

var_dump(imageantialias($image, true));
?>
--EXPECTF--
Warning: imageantialias(): supplied resource is not a valid Image resource in %s on line %d
bool(false)
