--TEST--
ZE2 You cannot overload a non static method with a static method
--SKIPIF--
<?php if (version_compare(zend_version(), '2.0.0-dev', '<')) die('skip ZendEngine 2 needed'); ?>
--FILE--
<?php

class pass {
	function show() {
		echo "Call to function pass::show()\n";
	}
}

class fail extends pass {
	static function show() {
		echo "Call to function fail::show()\n";
	}
}

$t = new pass();
$t->show();
fail::show();

echo "Done\n"; // shouldn't be displayed
?>
--EXPECTF--
Fatal error: Cannot make non static method pass::show() static in class fail in %s on line %d
