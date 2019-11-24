--TEST--
Test mcrypt_decrypt() function : basic functionality 
--SKIPIF--
<?php 
if (!extension_loaded("mcrypt")) {
	print "skip - mcrypt extension not loaded"; 
}	 
?>
--FILE--
<?php
/* Prototype  : string mcrypt_decrypt(string cipher, string key, string data, string mode, string iv)
 * Description: OFB crypt/decrypt data using key key with cipher cipher starting with iv 
 * Source code: ext/mcrypt/mcrypt.c
 * Alias to functions: 
 */

echo "*** Testing mcrypt_decrypt() : basic functionality ***\n";


// Initialise all required variables
$cipher = MCRYPT_3DES;
$mode = MCRYPT_MODE_CBC;

// tripledes uses keys with exactly 192 bits (24 bytes)
$keys = array(
   b'12345678', 
   b'12345678901234567890', 
   b'123456789012345678901234', 
   b'12345678901234567890123456'
);
$data1 = array(
   'IleMhoxiOthmHua4tFBHOw==',
   'EeF1s6C+w1IiHj1gdDn81g==',
   'EEuXpjZPueyYoG0LGQ199Q==',
   'EEuXpjZPueyYoG0LGQ199Q=='
);
// tripledes is a block cipher of 64 bits (8 bytes)
$ivs = array(
   b'1234', 
   b'12345678', 
   b'123456789'
);
$data2 = array(
   '+G7nGcWIxij3TZjpI9lJdQ==',
   '3bJiFMeyScxOLQcE6mZtLg==',
   '+G7nGcWIxij3TZjpI9lJdQ=='
);

$iv = b'12345678';
echo "\n--- testing different key lengths\n";
for ($i = 0; $i < sizeof($keys); $i++) {
   echo "\nkey length=".strlen($keys[$i])."\n";
   special_var_dump(mcrypt_decrypt($cipher, $keys[$i], base64_decode($data1[$i]), $mode, $iv));
}

$key = b'123456789012345678901234';
echo "\n--- testing different iv lengths\n";
for ($i = 0; $i < sizeof($ivs); $i++) {
   echo "\niv length=".strlen($ivs[$i])."\n";
   special_var_dump(mcrypt_decrypt($cipher, $key, base64_decode($data2[$i]), $mode, $ivs[$i]));
}

function special_var_dump($str) {
   var_dump(bin2hex($str));
}  
?>
===DONE===
--EXPECTF--
*** Testing mcrypt_decrypt() : basic functionality ***

--- testing different key lengths

key length=8

Deprecated: Function mcrypt_decrypt() is deprecated in %s%emcrypt_decrypt_3des_cbc.php on line 44

Warning: mcrypt_decrypt(): Key of size 8 not supported by this algorithm. Only keys of size 24 supported in %s on line %d
string(0) ""

key length=20

Deprecated: Function mcrypt_decrypt() is deprecated in %s%emcrypt_decrypt_3des_cbc.php on line 44

Warning: mcrypt_decrypt(): Key of size 20 not supported by this algorithm. Only keys of size 24 supported in %s on line %d
string(0) ""

key length=24

Deprecated: Function mcrypt_decrypt() is deprecated in %s%emcrypt_decrypt_3des_cbc.php on line 44
string(32) "736563726574206d6573736167650000"

key length=26

Deprecated: Function mcrypt_decrypt() is deprecated in %s%emcrypt_decrypt_3des_cbc.php on line 44

Warning: mcrypt_decrypt(): Key of size 26 not supported by this algorithm. Only keys of size 24 supported in %s on line %d
string(0) ""

--- testing different iv lengths

iv length=4

Deprecated: Function mcrypt_decrypt() is deprecated in %s%emcrypt_decrypt_3des_cbc.php on line 51

Warning: mcrypt_decrypt(): Received initialization vector of size 4, but size 8 is required for this encryption mode in %s on line %d
string(0) ""

iv length=8

Deprecated: Function mcrypt_decrypt() is deprecated in %s%emcrypt_decrypt_3des_cbc.php on line 51
string(32) "659ec947f4dc3a3b9c50de744598d3c8"

iv length=9

Deprecated: Function mcrypt_decrypt() is deprecated in %s%emcrypt_decrypt_3des_cbc.php on line 51

Warning: mcrypt_decrypt(): Received initialization vector of size 9, but size 8 is required for this encryption mode in %s on line %d
string(0) ""
===DONE===
