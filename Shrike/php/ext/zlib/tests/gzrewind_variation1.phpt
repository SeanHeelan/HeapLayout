--TEST--
Test function gzrewind() by calling it with its expected arguments when writing
--SKIPIF--
<?php 
if (!extension_loaded("zlib")) {
	print "skip - ZLIB extension not loaded"; 
}
?>
--FILE--
<?php
$f = "temp2.txt.gz";
$h = gzopen($f, 'w');
gzwrite($h, b'The first string.');
var_dump(gzrewind($h));
gzwrite($h, b'The second string.');
gzclose($h);

$h = gzopen($f, 'r');
gzpassthru($h);
gzclose($h);
unlink($f);
echo "\n";
?>
===DONE===
--EXPECT--
bool(false)
The first string.The second string.
===DONE===