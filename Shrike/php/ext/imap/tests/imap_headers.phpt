--TEST--
imap_headers() incorrect parameter count
--CREDITS--
Paul Sohier
#phptestfest utrecht
--SKIPIF--
<?php
require_once(dirname(__FILE__).'/skipif.inc');
?>
--FILE--
<?php
echo "Checking with no parameters\n";
imap_headers();

echo  "Checking with incorrect parameter type\n";
imap_headers('');
imap_headers(false);
?>
--EXPECTF--
Checking with no parameters

Warning: imap_headers() expects exactly 1 parameter, 0 given in %s on line %d
Checking with incorrect parameter type

Warning: imap_headers() expects parameter 1 to be resource, %unicode_string_optional% given in %s on line %d

Warning: imap_headers() expects parameter 1 to be resource, boolean given in %s on line %d

