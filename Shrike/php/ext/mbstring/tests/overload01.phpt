--TEST--
Function overloading test 1
--SKIPIF--
<?php 
	extension_loaded('mbstring') or die('skip mbstring not available'); 
	if (!function_exists("mail")) {
		die('skip mail() function is not available.');
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
var_dump(strlen($str));
var_dump(mb_strlen($str));
--EXPECT--
EUC-JP
int(33)
int(33)
