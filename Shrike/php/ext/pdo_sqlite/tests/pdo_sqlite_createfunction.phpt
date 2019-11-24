--TEST--
PDO_sqlite: Testing sqliteCreateFunction()
--SKIPIF--
<?php if (!extension_loaded('pdo_sqlite')) print 'skip not loaded'; ?>
--FILE--
<?php

$db = new pdo('sqlite::memory:');

$db->query('CREATE TABLE IF NOT EXISTS foobar (id INT AUTO INCREMENT, name TEXT)');

$db->query('INSERT INTO foobar VALUES (NULL, "PHP")');
$db->query('INSERT INTO foobar VALUES (NULL, "PHP6")');


$db->sqliteCreateFunction('testing', function($v) { return strtolower($v); });


foreach ($db->query('SELECT testing(name) FROM foobar') as $row) {
	var_dump($row);
}

$db->query('DROP TABLE foobar');

?>
--EXPECTF--
array(2) {
  ["testing(name)"]=>
  %string|unicode%(3) "php"
  [0]=>
  %string|unicode%(3) "php"
}
array(2) {
  ["testing(name)"]=>
  %string|unicode%(4) "php6"
  [0]=>
  %string|unicode%(4) "php6"
}
