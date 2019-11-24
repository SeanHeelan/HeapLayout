--TEST--
SPL: RegexIterator::getPregFlags() exception test
--CREDITS--
Lance Kesson jac_kesson@hotmail.com
#testfest London 2009-05-09
--FILE--
<?php

class myIterator implements Iterator {

function current (){}
function key ( ){}
function next ( ){}
function rewind ( ){}
function valid ( ){}


}

class TestRegexIterator extends RegexIterator{}

$rege = '/^a/';


$r = new TestRegexIterator(new myIterator, $rege);


try{	
	$r->setPregFlags();
}catch (Exception $e) {
	echo $e->getMessage();
}

?>
--EXPECTF--
Warning: RegexIterator::setPregFlags() expects exactly 1 parameter, 0 given in %s