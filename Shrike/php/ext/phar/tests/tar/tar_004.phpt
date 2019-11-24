--TEST--
Phar: tar-based phar, tar phar with stub, mapPhar()
--SKIPIF--
<?php
if (!extension_loaded("phar")) die("skip");
if (version_compare(PHP_VERSION, "6.0", "==")) die("skip pre-unicode version of PHP required");
if (!extension_loaded("spl")) die("skip SPL not available");
?>
--INI--
phar.readonly=0
phar.require_hash=0
--FILE--
<?php
include dirname(__FILE__) . '/files/tarmaker.php.inc';

$fname = dirname(__FILE__) . '/tar_004.phar.tar';
$alias = 'phar://' . $fname;

$tar = new tarmaker($fname, 'none');
$tar->init();
$tar->addFile('tar_004.php', '<?php var_dump(__FILE__);');
$tar->addFile('internal/file/here', "hi there!\n");
$tar->mkDir('internal/dir');
$tar->mkDir('dir');
$tar->addFile('.phar/stub.php', '<?php
Phar::mapPhar();
var_dump("it worked");
include "phar://" . __FILE__ . "/tar_004.php";
');
$tar->close();

include $fname;
?>
===DONE===
--CLEAN--
<?php
@unlink(dirname(__FILE__) . '/tar_004.phar.tar');
?>
--EXPECTF--
string(9) "it worked"
string(%d) "phar://%star_004.phar.tar/tar_004.php"
===DONE===