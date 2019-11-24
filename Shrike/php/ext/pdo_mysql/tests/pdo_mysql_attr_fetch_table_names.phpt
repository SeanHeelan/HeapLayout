--TEST--
PDO::ATTR_FETCH_TABLE_NAMES
--SKIPIF--
<?php
require_once(dirname(__FILE__) . DIRECTORY_SEPARATOR . 'skipif.inc');
require_once(dirname(__FILE__) . DIRECTORY_SEPARATOR . 'mysql_pdo_test.inc');
MySQLPDOTest::skip();
?>
--FILE--
<?php
	require_once(dirname(__FILE__) . DIRECTORY_SEPARATOR . 'mysql_pdo_test.inc');
	$db = MySQLPDOTest::factory();
	MySQLPDOTest::createTestTable($db);

	$db->setAttribute(PDO::ATTR_FETCH_TABLE_NAMES, 1);
	$stmt = $db->query('SELECT label FROM test LIMIT 1');
	var_dump($stmt->fetchAll(PDO::FETCH_ASSOC));
	$stmt->closeCursor();

	$db->setAttribute(PDO::ATTR_FETCH_TABLE_NAMES, 0);
	$stmt = $db->query('SELECT label FROM test LIMIT 1');
	var_dump($stmt->fetchAll(PDO::FETCH_ASSOC));
	$stmt->closeCursor();

	print "done!";
?>
--EXPECTF--
array(1) {
  [0]=>
  array(1) {
    [%u|b%"test.label"]=>
    %unicode|string%(1) "a"
  }
}
array(1) {
  [0]=>
  array(1) {
    [%u|b%"label"]=>
    %unicode|string%(1) "a"
  }
}
done!
