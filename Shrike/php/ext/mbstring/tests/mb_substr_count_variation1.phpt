--TEST--
Test mb_substr_count() function : usage variations - Pass different data types as $haystack arg
--SKIPIF--
<?php
extension_loaded('mbstring') or die('skip');
function_exists('mb_substr_count') or die("skip mb_substr_count() is not available in this build");
?>
--FILE--
<?php
/* Prototype  :int mb_substr_count(string $haystack, string $needle [, string $encoding])
 * Description: Count the number of substring occurrences 
 * Source code: ext/mbstring/mbstring.c
 */

/*
 * Pass different data types as $haystack argument to mb_substr_count() to test behaviour
 */

echo "*** Testing mb_substr_count() : usage variations ***\n";


// Initialise function arguments not being substituted
$needle = 'world';

//get an unset variable
$unset_var = 10;
unset ($unset_var);

// get a class
class classA
{
  public function __toString() {
    return "hello, world";
  }
}

// heredoc string
$heredoc = <<<EOT
hello, world
EOT;

// get a resource variable
$fp = fopen(__FILE__, "r");

// unexpected values to be passed to $haystack argument
$inputs = array(

       // int data
/*1*/  0,
       1,
       12345,
       -2345,

       // float data
/*5*/  10.5,
       -10.5,
       12.3456789000e10,
       12.3456789000E-10,
       .5,

       // null data
/*10*/ NULL,
       null,

       // boolean data
/*12*/ true,
       false,
       TRUE,
       FALSE,
       
       // empty data
/*16*/ "",
       '',

       // string data
/*18*/ "hello, world",
       'hello, world',
       $heredoc,
       
       // object data
/*21*/ new classA(),

       // undefined data
/*22*/ @$undefined_var,

       // unset data
/*23*/ @$unset_var,

       // resource variable
/*24*/ $fp
);

// loop through each element of $inputs to check the behavior of mb_substr_count()
$iterator = 1;
foreach($inputs as $input) {
  echo "\n-- Iteration $iterator --\n";
  var_dump( mb_substr_count($input, $needle) );
  $iterator++;
};

fclose($fp);


echo "Done";
?>
--EXPECTF--
*** Testing mb_substr_count() : usage variations ***

-- Iteration 1 --
int(0)

-- Iteration 2 --
int(0)

-- Iteration 3 --
int(0)

-- Iteration 4 --
int(0)

-- Iteration 5 --
int(0)

-- Iteration 6 --
int(0)

-- Iteration 7 --
int(0)

-- Iteration 8 --
int(0)

-- Iteration 9 --
int(0)

-- Iteration 10 --
int(0)

-- Iteration 11 --
int(0)

-- Iteration 12 --
int(0)

-- Iteration 13 --
int(0)

-- Iteration 14 --
int(0)

-- Iteration 15 --
int(0)

-- Iteration 16 --
int(0)

-- Iteration 17 --
int(0)

-- Iteration 18 --
int(1)

-- Iteration 19 --
int(1)

-- Iteration 20 --
int(1)

-- Iteration 21 --
int(1)

-- Iteration 22 --
int(0)

-- Iteration 23 --
int(0)

-- Iteration 24 --

Warning: mb_substr_count() expects parameter 1 to be string, resource given in %s on line %d
NULL
Done
