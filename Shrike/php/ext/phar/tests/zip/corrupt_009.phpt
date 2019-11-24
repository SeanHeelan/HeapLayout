--TEST--
Phar: corrupted zip (extra field way too long)
--SKIPIF--
<?php if (!extension_loaded("phar")) die("skip"); ?>
<?php if (!extension_loaded("spl")) die("skip SPL not available"); ?>
--FILE--
<?php
try {
	new PharData(dirname(__FILE__) . '/files/extralen_toolong.zip');
} catch (Exception $e) {
	echo $e->getMessage() . "\n";
}
?>
===DONE===
--EXPECTF--
phar error: Unable to process extra field header for file in central directory in zip-based phar "%sextralen_toolong.zip"
===DONE===
