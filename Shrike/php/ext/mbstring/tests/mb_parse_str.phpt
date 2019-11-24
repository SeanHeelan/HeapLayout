--TEST--
mb_parse_str()
--SKIPIF--
<?php extension_loaded('mbstring') or die('skip mbstring not available'); ?>
--FAIL--
register_globals calls killed the ability for mb_parse_str() to register into the global scope
--INI--
arg_separator.input=&
--FILE--
<?php
$queries = array(
	"foo=abc&bar=def",
	"%2bfoo=def&-bar=jkl",
	"foo[]=abc&foo[]=def&foo[]=ghi&bar[]=jkl"
);
function test($query) {
	$foo = '';
	$bar = '';
	mb_parse_str($query, $array);
	var_dump($array);
	var_dump($foo);
	var_dump($bar);
	mb_parse_str($query);
	var_dump($foo);
	var_dump($bar);
}
foreach ($queries as $query) {
	test($query);
}
?>
--EXPECT--
array(2) {
  ["foo"]=>
  string(3) "abc"
  ["bar"]=>
  string(3) "def"
}
string(0) ""
string(0) ""
string(3) "abc"
string(3) "def"
array(2) {
  ["+foo"]=>
  string(3) "def"
  ["-bar"]=>
  string(3) "jkl"
}
string(0) ""
string(0) ""
string(0) ""
string(0) ""
array(2) {
  ["foo"]=>
  array(3) {
    [0]=>
    string(3) "abc"
    [1]=>
    string(3) "def"
    [2]=>
    string(3) "ghi"
  }
  ["bar"]=>
  array(1) {
    [0]=>
    string(3) "jkl"
  }
}
string(0) ""
string(0) ""
array(3) {
  [0]=>
  string(3) "abc"
  [1]=>
  string(3) "def"
  [2]=>
  string(3) "ghi"
}
array(1) {
  [0]=>
  string(3) "jkl"
}
