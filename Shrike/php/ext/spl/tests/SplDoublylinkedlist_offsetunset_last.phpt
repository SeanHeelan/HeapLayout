--TEST--
SPL: SplDoublyLinkedList : offsetUnset - last element
--CREDITS--
PHPNW TestFest2009 - Rowan Merewood <rowan@merewood.org>
--FILE--
<?php
$list = new SplDoublyLinkedList();
$list->push('oh');
$list->push('hai');
$list->push('thar');
$list->offsetUnset(2);
var_dump($list);
?>
--EXPECTF--
object(SplDoublyLinkedList)#1 (2) {
  [%u|b%"flags":%u|b%"SplDoublyLinkedList":private]=>
  int(0)
  [%u|b%"dllist":%u|b%"SplDoublyLinkedList":private]=>
  array(2) {
    [0]=>
    %string|unicode%(2) "oh"
    [1]=>
    %string|unicode%(3) "hai"
  }
}
