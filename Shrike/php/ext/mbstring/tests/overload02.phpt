--TEST--
Function overloading test 2 
--SKIPIF--
<?php 
	extension_loaded('mbstring') or die('skip mbstring not available'); 
	if (!function_exists("mail")) {
		die('skip mail() function is not available.');
	}
	if (!function_exists("mb_ereg_replace")) {
		die('skip mb_ereg_replace() function is not available.');
	}
?>
--INI--
output_handler=
mbstring.func_overload=7
mbstring.internal_encoding=EUC-JP
--FILE--
<?php
echo mb_internal_encoding()."\n";

$ngchars = array('ǽ','ɽ','��','��');
$str = '��Ͻ�ܻ���Һ���ɽ��ǽ��ɽ��������˽��Ž�չ�ʸ����ͽ���Ƭ���ե���';
$converted_str = mb_convert_encoding($str, 'Shift_JIS');
mb_regex_encoding('Shift_JIS');
foreach($ngchars as $c) {
	$c = mb_convert_encoding($c, 'Shift_JIS');
	$replaced = mb_convert_encoding(str_replace($c, '!!', $converted_str), mb_internal_encoding(), 'Shift_JIS');
	var_dump(strpos($replaced, '!!'));
}
?>
--EXPECT--
EUC-JP
int(10)
int(8)
int(3)
int(29)
