--TEST--
Test date_sunrise() function : usage variation -  Passing high positive and negative float values to time argument.
--SKIPIF--
<?php if (PHP_INT_SIZE != 4) echo "skip this test is for 32-bit only"; ?>
--FILE--
<?php
/* Prototype  : mixed date_sunrise(mixed time [, int format [, float latitude [, float longitude [, float zenith [, float gmt_offset]]]]])
 * Description: Returns time of sunrise for a given day and location 
 * Source code: ext/date/php_date.c
 * Alias to functions: 
 */

echo "*** Testing date_sunrise() : usage variation ***\n";

// GMT is zero for the timezone
date_default_timezone_set("Asia/Calcutta");
//Initialise the variables
$latitude = 38.4;
$longitude = -9;
$zenith = 90;
$gmt_offset = 1;

echo "\n-- Testing date_sunrise() function by passing float 12.3456789000e10 value to time --\n";
$time = 12.3456789000e10;
var_dump( date_sunrise($time, SUNFUNCS_RET_STRING, $latitude, $longitude, $zenith, $gmt_offset) );
var_dump( date_sunrise($time, SUNFUNCS_RET_DOUBLE, $latitude, $longitude, $zenith, $gmt_offset) );
var_dump( date_sunrise($time, SUNFUNCS_RET_TIMESTAMP, $latitude, $longitude, $zenith, $gmt_offset) );

echo "\n-- Testing date_sunrise() function by passing float -12.3456789000e10 value to time --\n";
$time = -12.3456789000e10;
var_dump( date_sunrise($time, SUNFUNCS_RET_STRING, $latitude, $longitude, $zenith, $gmt_offset) );
var_dump( date_sunrise($time, SUNFUNCS_RET_DOUBLE, $latitude, $longitude, $zenith, $gmt_offset) );
var_dump( date_sunrise($time, SUNFUNCS_RET_TIMESTAMP, $latitude, $longitude, $zenith, $gmt_offset) );

?>
===DONE===
--EXPECTF--
*** Testing date_sunrise() : usage variation ***

-- Testing date_sunrise() function by passing float 12.3456789000e10 value to time --

Warning: date_sunrise() expects parameter 1 to be integer, float given in %s on line %d
bool(false)

Warning: date_sunrise() expects parameter 1 to be integer, float given in %s on line %d
bool(false)

Warning: date_sunrise() expects parameter 1 to be integer, float given in %s on line %d
bool(false)

-- Testing date_sunrise() function by passing float -12.3456789000e10 value to time --

Warning: date_sunrise() expects parameter 1 to be integer, float given in %s on line %d
bool(false)

Warning: date_sunrise() expects parameter 1 to be integer, float given in %s on line %d
bool(false)

Warning: date_sunrise() expects parameter 1 to be integer, float given in %s on line %d
bool(false)
===DONE===