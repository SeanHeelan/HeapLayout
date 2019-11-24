--TEST--
SPL: CachingIterator and __toString and flags = 0
--FILE--
<?php

function test($it)
{
	foreach($it as $v)
	{
		var_dump((string)$it);
	}
}

$ar = new ArrayIterator(array(1, 2, 3));

test(new CachingIterator($ar, 0));

?>
===DONE===
--EXPECTF--	

Fatal error: Method CachingIterator::__toString() must not throw an exception, caught BadMethodCallException: CachingIterator does not fetch string value (see CachingIterator::__construct) in %siterator_036.php on line %d
