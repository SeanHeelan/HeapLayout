--TEST--
Bug #73668: "SIGFPE Arithmetic exception" in opcache when divide by minus 1
--FILE--
<?php
$a/-1;
?>
--EXPECTF--
Notice: Undefined variable: a in %s on line %d
