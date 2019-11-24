--TEST--
SPL: ArrayObject with bad iterator class.
--FILE--
<?php
try {
  $ao = new ArrayObject(array('a'=>1,'b'=>2,'c'=>3));
  $ao->setIteratorClass("nonExistentClass");
  foreach($ao as $key=>$value) {
    echo "  $key=>$value\n";
  }
} catch (Exception $e) {
	var_dump($e->getMessage());
}

try {
  $ao = new ArrayObject(array('a'=>1,'b'=>2,'c'=>3));
  $ao->setIteratorClass("stdClass");
  foreach($ao as $key=>$value) {
    echo "  $key=>$value\n";
  }
} catch (Exception $e) {
	var_dump($e->getMessage());
}


try {
  $ao = new ArrayObject(array('a'=>1,'b'=>2,'c'=>3), 0, "nonExistentClass");
  foreach($ao as $key=>$value) {
    echo "  $key=>$value\n";
  }
} catch (TypeError $e) {
	var_dump($e->getMessage());
}

try {
  $ao = new ArrayObject(array('a'=>1,'b'=>2,'c'=>3), 0, "stdClass");
  foreach($ao as $key=>$value) {
    echo "  $key=>$value\n";
  }
} catch (TypeError $e) {
	var_dump($e->getMessage());
}

?>
--EXPECTF--
Warning: ArrayObject::setIteratorClass() expects parameter 1 to be a class name derived from Iterator, 'nonExistentClass' given in %s on line 4
  a=>1
  b=>2
  c=>3

Warning: ArrayObject::setIteratorClass() expects parameter 1 to be a class name derived from Iterator, 'stdClass' given in %s on line 14
  a=>1
  b=>2
  c=>3
string(113) "ArrayObject::__construct() expects parameter 3 to be a class name derived from Iterator, 'nonExistentClass' given"
string(105) "ArrayObject::__construct() expects parameter 3 to be a class name derived from Iterator, 'stdClass' given"
