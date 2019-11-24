--TEST--
IntlCalendar::setMinimalDaysInFirstWeek(): bad arguments
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

var_dump($c->setMinimalDaysInFirstWeek());
var_dump($c->setMinimalDaysInFirstWeek(1, 2));
var_dump($c->setMinimalDaysInFirstWeek(0));

var_dump(intlcal_set_minimal_days_in_first_week($c, 0));
var_dump(intlcal_set_minimal_days_in_first_week(1, 2));

--EXPECTF--
Warning: IntlCalendar::setMinimalDaysInFirstWeek() expects exactly 1 parameter, 0 given in %s on line %d

Warning: IntlCalendar::setMinimalDaysInFirstWeek(): intlcal_set_minimal_days_in_first_week: bad arguments in %s on line %d
bool(false)

Warning: IntlCalendar::setMinimalDaysInFirstWeek() expects exactly 1 parameter, 2 given in %s on line %d

Warning: IntlCalendar::setMinimalDaysInFirstWeek(): intlcal_set_minimal_days_in_first_week: bad arguments in %s on line %d
bool(false)

Warning: IntlCalendar::setMinimalDaysInFirstWeek(): intlcal_set_minimal_days_in_first_week: invalid number of days; must be between 1 and 7 in %s on line %d
bool(false)

Warning: intlcal_set_minimal_days_in_first_week(): intlcal_set_minimal_days_in_first_week: invalid number of days; must be between 1 and 7 in %s on line %d
bool(false)

Fatal error: Uncaught TypeError: Argument 1 passed to intlcal_set_minimal_days_in_first_week() must be an instance of IntlCalendar, integer given in %s:%d
Stack trace:
#0 %s(%d): intlcal_set_minimal_days_in_first_week(1, 2)
#1 {main}
  thrown in %s on line %d

