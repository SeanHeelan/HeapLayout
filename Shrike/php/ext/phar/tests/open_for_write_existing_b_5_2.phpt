--TEST--
Phar: fopen a .phar for writing (existing file)
--SKIPIF--
<?php if (!extension_loaded("phar")) die("skip"); ?>
<?php if (version_compare(PHP_VERSION, "5.3", ">")) die("skip requires 5.2 or earlier"); ?>
--INI--
phar.readonly=1
phar.require_hash=0
--FILE--
<?php
$fname = dirname(__FILE__) . '/' . basename(__FILE__, '.php') . '.phar.php';
$pname = 'phar://' . $fname;
$file = "<?php __HALT_COMPILER(); ?>";

$files = array();
$files['a.php'] = '<?php echo "This is a\n"; ?>';
$files['b.php'] = '<?php echo "This is b\n"; ?>';
$files['b/c.php'] = '<?php echo "This is b/c\n"; ?>';
include 'files/phar_test.inc';

function err_handler($errno, $errstr, $errfile, $errline) {
  echo "Recoverable fatal error: $errstr in $errfile on line $errline\n";
}

set_error_handler("err_handler", E_RECOVERABLE_ERROR);

$fp = fopen($pname . '/b/c.php', 'wb');
fwrite($fp, 'extra');
fclose($fp);
include $pname . '/b/c.php';
?>
===DONE===
--CLEAN--
<?php unlink(dirname(__FILE__) . '/' . basename(__FILE__, '.clean.php') . '.phar.php'); ?>
--EXPECTF--

Warning: fopen(phar://%sopen_for_write_existing_b_5_2.phar.php/b/c.php): failed to open stream: phar error: write operations disabled by the php.ini setting phar.readonly in %sopen_for_write_existing_b_5_2.php on line %d

Warning: fwrite(): supplied argument is not a valid stream resource in %spen_for_write_existing_b_5_2.php on line %d

Warning: fclose(): supplied argument is not a valid stream resource in %spen_for_write_existing_b_5_2.php on line %d
This is b/c
===DONE===
