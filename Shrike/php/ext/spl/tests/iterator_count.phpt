--TEST--
SPL: iterator_count() exceptions test
--CREDITS--
Lance Kesson jac_kesson@hotmail.com
#testfest London 2009-05-09
--FILE--
<?php
$array=array('a','b');

$iterator = new ArrayIterator($array);

iterator_count();


iterator_count($iterator,'1');

iterator_count('1');


?>
--EXPECTF--
Warning: iterator_count() expects exactly 1 parameter, 0 given in %s

Warning: iterator_count() expects exactly 1 parameter, 2 given in %s

Fatal error: Uncaught TypeError: Argument 1 passed to iterator_count() must implement interface Traversable, string given in %s:%d
Stack trace:
#0 %s(%d): iterator_count('1')
#1 {main}
  thrown in %s on line %d
