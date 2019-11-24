--TEST--
SQLite3::createFunction - Basic test
--SKIPIF--
<?php require_once(dirname(__FILE__) . '/skipif.inc'); ?>
--FILE--
<?php

require_once(dirname(__FILE__) . '/new_db.inc');

$func = 'strtoupper';
var_dump($db->createfunction($func, $func));
var_dump($db->querySingle('SELECT strtoupper("test")'));

$func2 = 'strtolower';
var_dump($db->createfunction($func2, $func2));
var_dump($db->querySingle('SELECT strtolower("TEST")'));

var_dump($db->createfunction($func, $func2));
var_dump($db->querySingle('SELECT strtoupper("tEst")'));


?>
--EXPECTF--
bool(true)
%string|unicode%(4) "TEST"
bool(true)
%string|unicode%(4) "test"
bool(true)
%string|unicode%(4) "test"
