--TEST--
mb_output_handler() (Shift_JIS)
--SKIPIF--
<?php extension_loaded('mbstring') or die('skip mbstring not available'); ?>
--INI--
output_handler=mb_output_handler
mbstring.internal_encoding=Shift_JIS
mbstring.http_output=EUC-JP
--FILE--
<?php
// Shift_JIS
var_dump("�e�X�g�p���{�ꕶ����B���̃��W���[����PHP�Ƀ}���`�o�C�g�֐���񋟂��܂��B");
?>

--EXPECT--
string(73) "�ƥ��������ܸ�ʸ���󡣤��Υ⥸�塼���PHP�˥ޥ���Х��ȴؿ����󶡤��ޤ���"
