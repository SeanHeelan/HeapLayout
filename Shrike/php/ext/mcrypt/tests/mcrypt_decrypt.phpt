--TEST--
mcrypt_decrypt
--SKIPIF--
<?php if (!extension_loaded("mcrypt")) print "skip"; ?>
--FILE--
<?php
$key      = "0123456789012345";
$secret   = "PHP Testfest 2008";
$mode     = MCRYPT_MODE_CBC;
$cipher   = MCRYPT_RIJNDAEL_128;

$iv       = mcrypt_create_iv(mcrypt_get_iv_size($cipher, $mode), MCRYPT_RAND);
$enc_data = mcrypt_encrypt($cipher, $key, $secret, $mode, $iv);

// we have to trim as AES rounds the blocks and decrypt doesnt detect that
echo trim(mcrypt_decrypt($cipher, $key, $enc_data, $mode, $iv)) . "\n";

// a warning must be issued if we don't use a IV on a AES cipher, that usually requires an IV
var_dump(mcrypt_decrypt($cipher, $key, $enc_data, MCRYPT_MODE_CBC));

var_dump(mcrypt_decrypt(MCRYPT_BLOWFISH, "FooBar", $enc_data, MCRYPT_MODE_CBC, $iv));
--EXPECTF--
Deprecated: Function mcrypt_get_iv_size() is deprecated in %s%emcrypt_decrypt.php on line 7

Deprecated: Function mcrypt_create_iv() is deprecated in %s%emcrypt_decrypt.php on line 7

Deprecated: Function mcrypt_encrypt() is deprecated in %s%emcrypt_decrypt.php on line 8

Deprecated: Function mcrypt_decrypt() is deprecated in %s%emcrypt_decrypt.php on line 11
PHP Testfest 2008

Deprecated: Function mcrypt_decrypt() is deprecated in %s%emcrypt_decrypt.php on line 14

Warning: mcrypt_decrypt(): Encryption mode requires an initialization vector of size 16 in %s on line %d
bool(false)

Deprecated: Function mcrypt_decrypt() is deprecated in %s%emcrypt_decrypt.php on line 16

Warning: mcrypt_decrypt(): Received initialization vector of size 16, but size 8 is required for this encryption mode in %s on line %d
bool(false)
