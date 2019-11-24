--TEST--
Exercise OCIPing functionality on reconnect (code coverage test)
--SKIPIF--
<?php if (!extension_loaded('oci8')) die ("skip no oci8 extension"); ?>
--INI--
oci8.ping_interval=0
--FILE--
<?php

require(dirname(__FILE__).'/details.inc');

for ($i = 0; $i < 2; $i++) {
	if (!empty($dbase)) {
		$c = oci_pconnect($user,$password,$dbase);
	}
	else {
		$c = oci_pconnect($user,$password);
	}
}

echo "Done\n";

?>
--EXPECTF--
Done
