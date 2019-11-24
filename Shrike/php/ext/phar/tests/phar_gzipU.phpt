--TEST--
Phar: gzipped phar
--SKIPIF--
<?php
if (!extension_loaded("phar")) die("skip");
if (version_compare(PHP_VERSION, "6.0", "!=")) die("skip Unicode support required");
if (!extension_loaded("spl")) die("skip SPL not available");
if (!extension_loaded("zlib")) die("skip zlib not available");
if (version_compare(phpversion(), '5.2.6', '<')) die("skip zlib is buggy in PHP < 5.2.6");
?>
--INI--
phar.readonly=0
phar.require_hash=0
--FILE--
<?php
$fname = dirname(__FILE__) . '/phar_gzip.phar';
$pname = 'phar://' . $fname;
$fname2 = dirname(__FILE__) . '/phar_gzip.2.phar';
$pname2 = 'phar://' . $fname2;

$file = '<?php
Phar::mapPhar();
var_dump("it worked");
include "phar://" . __FILE__ . "/tar_004.php";
__HALT_COMPILER();';

$files = array();
$files['tar_004.php']   = '<?php var_dump(__FILE__);';
$files['internal/file/here']   = "hi there!\n";
$files['internal/dir/'] = '';
$files['dir/'] = '';
$gzip = true;

include 'files/phar_test.inc';

include $fname;

$a = new Phar($fname);
$a['test'] = 'hi';
copy($fname, $fname2);
$a->setAlias('another');
$b = new Phar($fname2);
var_dump($b->isFileFormat(Phar::PHAR));
var_dump($b->isCompressed() == Phar::GZ);
?>
===DONE===
--CLEAN--
<?php
@unlink(dirname(__FILE__) . '/phar_gzip.phar');
@unlink(dirname(__FILE__) . '/phar_gzip.2.phar');
?>
--EXPECTF--
unicode(9) "it worked"
unicode(%d) "phar://%sphar_gzip.phar/tar_004.php"
bool(true)
bool(true)
===DONE===