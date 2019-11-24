--TEST--
Phar: fopen a .phar for writing (new file) zip-based
--SKIPIF--
<?php if (!extension_loaded("phar")) die("skip"); ?>
<?php if (version_compare(PHP_VERSION, "5.3", ">")) die("skip requires 5.2 or earlier"); ?>
--INI--
phar.readonly=0
phar.require_hash=0
--FILE--
<?php

$fname = dirname(__FILE__) . '/' . basename(__FILE__, '.php') . '.phar.zip';
$alias = 'phar://' . $fname;

$phar = new Phar($fname);
$phar->setStub('<?php __HALT_COMPILER(); ?>');

$files = array();

$files['a.php'] = '<?php echo "This is a\n"; ?>';
$files['b.php'] = '<?php echo "This is b\n"; ?>';
$files['b/c.php'] = '<?php echo "This is b/c\n"; ?>';

foreach ($files as $n => $file) {
	$phar[$n] = $file;
}
$phar->stopBuffering();

ini_set('phar.readonly', 1);

function err_handler($errno, $errstr, $errfile, $errline) {
  echo "Recoverable fatal error: $errstr in $errfile on line $errline\n";
}

set_error_handler("err_handler", E_RECOVERABLE_ERROR);

$fp = fopen($alias . '/b/new.php', 'wb');
fwrite($fp, 'extra');
fclose($fp);

include $alias . '/b/c.php';
include $alias . '/b/new.php';
?>

===DONE===
--CLEAN--
<?php unlink(dirname(__FILE__) . '/' . basename(__FILE__, '.clean.php') . '.phar.zip'); ?>
--EXPECTF--

Warning: fopen(phar://%sopen_for_write_newfile_b_5_2.phar.zip/b/new.php): failed to open stream: phar error: write operations disabled by the php.ini setting phar.readonly in %sopen_for_write_newfile_b_5_2.php on line %d

Warning: fwrite(): supplied argument is not a valid stream resource in %sopen_for_write_newfile_b_5_2.php on line %d

Warning: fclose(): supplied argument is not a valid stream resource in %sopen_for_write_newfile_b_5_2.php on line %d
This is b/c

Warning: include(phar://%sopen_for_write_newfile_b_5_2.phar.zip/b/new.php): failed to open stream: phar error: "b/new.php" is not a file in phar "%sopen_for_write_newfile_b_5_2.phar.zip" in %sopen_for_write_newfile_b_5_2.php on line %d

Warning: include(): Failed opening 'phar://%sopen_for_write_newfile_b_5_2.phar.zip/b/new.php' for inclusion (include_path='%s') in %sopen_for_write_newfile_b_5_2.php on line %d

===DONE===
