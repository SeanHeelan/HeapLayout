--TEST--
Phar: test stat function interceptions and is_file/is_link edge cases (PHP 5.2)
--SKIPIF--
<?php if (!extension_loaded("phar")) die("skip");?>
<?php if (substr(phpversion(), 0, 3) != '5.2') die("skip PHP 5.2 required for this test");?>
--INI--
phar.readonly=0
phar.require_hash=0
--FILE--
<?php
Phar::interceptFileFuncs();
is_file();
is_link();
var_dump(is_file(__FILE__));

$fname2 = dirname(__FILE__) . '/' . basename(__FILE__, '.php') . '.tar';
$fname3 = dirname(__FILE__) . '/' . basename(__FILE__, '.php') . '.phar.tar';
copy(dirname(__FILE__) . '/tar/files/links.tar', $fname2);
$a = new PharData($fname2);
$b = $a->convertToExecutable();
unset($a);
Phar::unlinkArchive($fname2);
$b['foo/stat.php'] = '<?php
echo "is_link\n";
var_dump(is_link("./stat.php"),is_file("./stat.php"), is_link("./oops"), is_file("./oops"));
var_dump(is_link("testit/link"), filetype("testit/link"), filetype("testit"), is_file("testit/link"));
echo "not found\n";
var_dump(is_link("notfound"));
echo "dir\n";
var_dump(is_dir("./bar"), is_file("foo/bar/blah"));
?>';
$b->addEmptyDir('foo/bar/blah');
$b->setStub('<?php
include "phar://" . __FILE__ . "/foo/stat.php";
__HALT_COMPILER();');
include $fname3;
?>
===DONE===
--CLEAN--
<?php unlink(dirname(__FILE__) . '/' . basename(__FILE__, '.clean.php') . '.phar.tar'); ?>
<?php unlink(dirname(__FILE__) . '/' . basename(__FILE__, '.clean.php') . '.tar'); ?>
--EXPECTF--
Warning: Wrong parameter count for is_file() in %sstat2.php on line %d

Warning: Wrong parameter count for is_link() in %sstat2.php on line %d
bool(true)
is_link
bool(false)
bool(true)
bool(false)
bool(false)
bool(true)
string(4) "link"
string(3) "dir"
bool(true)
not found
bool(false)
dir
bool(true)
bool(false)
===DONE===