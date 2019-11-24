--TEST--
Bug #73646 (mb_ereg_search_init null pointer dereference)
--FILE--
<?php

$v1=str_repeat("#", -1);
var_dump(mb_ereg_search_init($v1));
?>
--EXPECTF--
Warning: str_repeat(): Second argument has to be greater than or equal to 0 in %sbug73646.php on line %d
bool(true)
