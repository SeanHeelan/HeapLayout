--TEST--
Test posix_getgrgid() function : usage variations  - parameter types
--SKIPIF--
<?php
    PHP_INT_SIZE == 4 or die("skip - 32-bit only");
	if(!extension_loaded("posix")) print "skip - POSIX extension not loaded"; 
?>
--FILE--
<?php
/* Prototype  : proto array posix_getgrgid(long gid)
 * Description: Group database access (POSIX.1, 9.2.1) 
 * Source code: ext/posix/posix.c
 * Alias to functions: 
 */

echo "*** Testing posix_getgrgid() : usage variations ***\n";

// Initialise function arguments not being substituted (if any)

//get an unset variable
$unset_var = 10;
unset ($unset_var);

//array of values to iterate over
$values = array(

      // float data
      10.5,
      -10.5,
      10.1234567e10,
      10.7654321E-10,
      .5,

      // array data
      array(),
      array(0),
      array(1),
      array(1, 2),
      array('color' => 'red', 'item' => 'pen'),

      // null data
      NULL,
      null,

      // boolean data
      true,
      false,
      TRUE,
      FALSE,

      // empty data
      "",
      '',

      // string data
      "string",
      'string',

      // undefined data
      $undefined_var,

      // unset data
      $unset_var,

      // object data
      new stdclass(),
);

// loop through each element of the array for gid

foreach($values as $value) {
      echo "\nArg value $value \n";
      $result = posix_getgrgid($value);
      if ((is_array($result) && (count($result) == 4)) 
          || 
          ($result === false)) {
          echo "valid output\n";
      } else {
          var_dump($result);
      }
};

echo "Done";
?>
--EXPECTF--
*** Testing posix_getgrgid() : usage variations ***

Notice: Undefined variable: undefined_var in %s on line %d

Notice: Undefined variable: unset_var in %s on line %d

Arg value 10.5 
valid output

Arg value -10.5 
valid output

Arg value 101234567000 

Warning: posix_getgrgid() expects parameter 1 to be integer, float given in %s on line %d
valid output

Arg value 1.07654321E-9 
valid output

Arg value 0.5 
valid output

Notice: Array to string conversion in %sposix_getgrgid_variation.php on line %d

Arg value Array 

Warning: posix_getgrgid() expects parameter 1 to be integer, array given in %s on line %d
valid output

Notice: Array to string conversion in %sposix_getgrgid_variation.php on line %d

Arg value Array 

Warning: posix_getgrgid() expects parameter 1 to be integer, array given in %s on line %d
valid output

Notice: Array to string conversion in %sposix_getgrgid_variation.php on line %d

Arg value Array 

Warning: posix_getgrgid() expects parameter 1 to be integer, array given in %s on line %d
valid output

Notice: Array to string conversion in %sposix_getgrgid_variation.php on line %d

Arg value Array 

Warning: posix_getgrgid() expects parameter 1 to be integer, array given in %s on line %d
valid output

Notice: Array to string conversion in %sposix_getgrgid_variation.php on line %d

Arg value Array 

Warning: posix_getgrgid() expects parameter 1 to be integer, array given in %s on line %d
valid output

Arg value  
valid output

Arg value  
valid output

Arg value 1 
valid output

Arg value  
valid output

Arg value 1 
valid output

Arg value  
valid output

Arg value  

Warning: posix_getgrgid() expects parameter 1 to be integer, string given in %s on line %d
valid output

Arg value  

Warning: posix_getgrgid() expects parameter 1 to be integer, string given in %s on line %d
valid output

Arg value string 

Warning: posix_getgrgid() expects parameter 1 to be integer, string given in %s on line %d
valid output

Arg value string 

Warning: posix_getgrgid() expects parameter 1 to be integer, string given in %s on line %d
valid output

Arg value  
valid output

Arg value  
valid output

Recoverable fatal error: Object of class stdClass could not be converted to string in %s on line %d
