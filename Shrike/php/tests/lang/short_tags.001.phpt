--TEST--
short_open_tag: On
--INI--
short_open_tag=on
--FILE--
<?
echo "Used a short tag\n";
?>
Finished
--EXPECT--
Used a short tag
Finished
