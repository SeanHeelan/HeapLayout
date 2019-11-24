--TEST--
Testing null byte injection in imagewbmp
--CLEAN--
$tempdir = sys_get_temp_dir(). '/php-gdtest';
foreach (glob($tempdir . "/test*") as $file ) { unlink($file); }
rmdir($tempdir);
--SKIPIF--
<?php
if(!extension_loaded('gd')){ die('skip gd extension not available'); }
$support = gd_info();
if (!isset($support['WBMP Support']) || $support['WBMP Support'] === false) {
	print 'skip wbmp support not available';
}
?>
--FILE--
<?php
$image = imagecreate(1,1);// 1px image


$tempdir = sys_get_temp_dir(). '/php-gdtest';
if (!file_exists($tempdir) && !is_dir($tempdir)) {
	mkdir ($tempdir, 0777, true);
}

$userinput = "1\0"; // from post or get data
$temp = $tempdir. "/test" . $userinput .".tmp";

echo "\nimagewbmp TEST\n";
imagewbmp($image, $temp);
var_dump(file_exists($tempdir. "/test1"));
var_dump(file_exists($tempdir. "/test1.tmp"));
foreach (glob($tempdir . "/test*") as $file ) { unlink($file); }

--EXPECTF--
imagewbmp TEST

Warning: imagewbmp(): Invalid 2nd parameter, filename must not contain null bytes in %s on line %d
bool(false)
bool(false)
