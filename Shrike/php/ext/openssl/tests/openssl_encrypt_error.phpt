--TEST--
openssl_encrypt() error tests
--SKIPIF--
<?php if (!extension_loaded("openssl")) print "skip"; ?>
--FILE--
<?php
$data = "openssl_encrypt() tests";
$method = "AES-128-CBC";
$password = "openssl";
$iv = str_repeat("\0", openssl_cipher_iv_length($method));
$wrong = "wrong";
$object = new stdclass;
$arr = array(1);

// wrong paramters tests
var_dump(openssl_encrypt($data, $wrong, $password));
var_dump(openssl_encrypt($object, $method, $password));
var_dump(openssl_encrypt($data, $object, $password));
var_dump(openssl_encrypt($data, $method, $object));
var_dump(openssl_encrypt($arr, $method, $object));
var_dump(openssl_encrypt($data, $arr, $object));
var_dump(openssl_encrypt($data, $method, $arr));

// invalid using of an authentication tag
var_dump(openssl_encrypt($data, $method, $password, 0, $iv, $wrong));
?>
--EXPECTF--
Warning: openssl_encrypt(): Unknown cipher algorithm in %s on line %d
bool(false)

Warning: openssl_encrypt() expects parameter 1 to be string, object given in %s on line %d
NULL

Warning: openssl_encrypt() expects parameter 2 to be string, object given in %s on line %d
NULL

Warning: openssl_encrypt() expects parameter 3 to be string, object given in %s on line %d
NULL

Warning: openssl_encrypt() expects parameter 1 to be string, array given in %s on line %d
NULL

Warning: openssl_encrypt() expects parameter 2 to be string, array given in %s on line %d
NULL

Warning: openssl_encrypt() expects parameter 3 to be string, array given in %s on line %d
NULL

Warning: openssl_encrypt(): The authenticated tag cannot be provided for cipher that doesn not support AEAD in %s on line %d
string(44) "iPR4HulskuaP5Z6me5uImk6BqVyJG73+63tkPauVZYk="
