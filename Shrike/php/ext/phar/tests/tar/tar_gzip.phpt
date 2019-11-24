--TEST--
Phar: tar-based phar, gzipped tar
--SKIPIF--
<?php
if (!extension_loaded("phar")) die("skip");
if (version_compare(PHP_VERSION, "6.0", "==")) die("skip pre-unicode version of PHP required");
if (!extension_loaded("spl")) die("skip SPL not available");
if (!extension_loaded("zlib")) die("skip zlib not available");
if (version_compare(phpversion(), '5.2.6', '<')) die("skip zlib is buggy in PHP < 5.2.6");
?>
--INI--
phar.readonly=0
phar.require_hash=0
--FILE--
<?php
include dirname(__FILE__) . '/files/tarmaker.php.inc';
$fname = dirname(__FILE__) . '/tar_gzip.phar';
$pname = 'phar://' . $fname;
$fname2 = dirname(__FILE__) . '/tar_gzip.phar.tar';
$pname2 = 'phar://' . $fname2;

$a = new tarmaker($fname, 'zlib');
$a->init();
$a->addFile('tar_004.php', '<?php var_dump(__FILE__);');
$a->addFile('internal/file/here', "hi there!\n");
$a->mkDir('internal/dir');
$a->mkDir('dir');
$a->addFile('.phar/stub.php', '<?php
Phar::mapPhar();
var_dump("it worked");
include "phar://" . __FILE__ . "/tar_004.php";
');
$a->close();

include $fname;

$a = new Phar($fname);
$a['test'] = 'hi';
copy($fname, $fname2);
$b = new Phar($fname2);
var_dump($b->isFileFormat(Phar::TAR));
var_dump($b->isCompressed() == Phar::GZ);
?>
===DONE===
--CLEAN--
<?php
@unlink(dirname(__FILE__) . '/tar_gzip.phar');
@unlink(dirname(__FILE__) . '/tar_gzip.phar.tar');
?>
--EXPECTF--
string(9) "it worked"
string(%d) "phar://%star_gzip.phar/tar_004.php"
bool(true)
bool(true)
===DONE===