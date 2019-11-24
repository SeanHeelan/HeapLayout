--TEST--
ldap_parse_result() - Basic ldap_parse_result test
--CREDITS--
Patrick Allaert <patrickallaert@php.net>
# Belgian PHP Testfest 2009
--SKIPIF--
<?php require_once('skipif.inc'); ?>
<?php require_once('skipifbindfailure.inc'); ?>
--FILE--
<?php
require "connect.inc";

$link = ldap_connect_and_bind($host, $port, $user, $passwd, $protocol_version);
insert_dummy_data($link, $base);
ldap_add($link, "cn=userref,$base", array(
        "objectClass" => array("extensibleObject", "referral"),
        "cn" => "userref",
        "ref" => "cn=userA,$base",
));
$result = ldap_search($link, "cn=userref,$base", "(cn=user*)");
$errcode = $dn = $errmsg = $refs =  null;
var_dump(
	ldap_parse_result($link, $result, $errcode, $dn, $errmsg, $refs),
	$errcode, $dn, $errmsg, $refs
);
?>
===DONE===
--CLEAN--
<?php
include "connect.inc";

$link = ldap_connect_and_bind($host, $port, $user, $passwd, $protocol_version);
// Referral can only be removed with Manage DSA IT Control
ldap_set_option($link, LDAP_OPT_SERVER_CONTROLS, array(array("oid" => "2.16.840.1.113730.3.4.2")));
ldap_delete($link, "cn=userref,$base");
remove_dummy_data($link, $base);
?>
--EXPECTF--
bool(true)
int(10)
string(%d) "cn=userref,%s"
string(0) ""
array(1) {
  [0]=>
  string(%d) "cn=userA,%s"
}
===DONE===
