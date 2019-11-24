--TEST--
mcrypt_enc_get_block_size
--SKIPIF--
<?php if (!extension_loaded("mcrypt")) print "skip"; ?>
--FILE--
<?php
$td = mcrypt_module_open(MCRYPT_RIJNDAEL_256, '', MCRYPT_MODE_CBC, '');
var_dump(mcrypt_enc_get_block_size($td));
$td = mcrypt_module_open(MCRYPT_3DES, '', MCRYPT_MODE_CBC, '');
var_dump(mcrypt_enc_get_block_size($td));
$td = mcrypt_module_open(MCRYPT_WAKE, '', MCRYPT_MODE_STREAM, '');
var_dump(mcrypt_enc_get_block_size($td));
--EXPECTF--
Deprecated: Function mcrypt_module_open() is deprecated in %s%emcrypt_enc_get_block_size.php on line 2

Deprecated: Function mcrypt_enc_get_block_size() is deprecated in %s%emcrypt_enc_get_block_size.php on line 3
int(32)

Deprecated: Function mcrypt_module_open() is deprecated in %s%emcrypt_enc_get_block_size.php on line 4

Deprecated: Function mcrypt_enc_get_block_size() is deprecated in %s%emcrypt_enc_get_block_size.php on line 5
int(8)

Deprecated: Function mcrypt_module_open() is deprecated in %s%emcrypt_enc_get_block_size.php on line 6

Deprecated: Function mcrypt_enc_get_block_size() is deprecated in %s%emcrypt_enc_get_block_size.php on line 7
int(1)
