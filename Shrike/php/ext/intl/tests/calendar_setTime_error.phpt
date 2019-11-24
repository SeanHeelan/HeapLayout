--TEST--
IntlCalendar::setTime(): bad arguments
--INI--
date.timezone=Atlantic/Azores
--SKIPIF--
<?php
if (!extension_loaded('intl'))
	die('skip intl extension not enabled');
--FILE--
<?php
ini_set("intl.error_level", E_WARNING);

$c = new IntlGregorianCalendar(NULL, 'pt_PT');

var_dump($c->setTime(1, 2));
var_dump($c->setTime("jjj"));

var_dump(intlcal_set_time($c, 1, 2));
var_dump(intlcal_set_time(1));
--EXPECTF--

Warning: IntlCalendar::setTime() expects exactly 1 parameter, 2 given in %s on line %d

Warning: IntlCalendar::setTime(): intlcal_set_time: bad arguments in %s on line %d
bool(false)

Warning: IntlCalendar::setTime() expects parameter 1 to be float, string given in %s on line %d

Warning: IntlCalendar::setTime(): intlcal_set_time: bad arguments in %s on line %d
bool(false)

Warning: intlcal_set_time() expects exactly 2 parameters, 3 given in %s on line %d

Warning: intlcal_set_time(): intlcal_set_time: bad arguments in %s on line %d
bool(false)

Fatal error: Uncaught TypeError: Argument 1 passed to intlcal_set_time() must be an instance of IntlCalendar, integer given in %s:%d
Stack trace:
#0 %s(%d): intlcal_set_time(1)
#1 {main}
  thrown in %s on line %d
