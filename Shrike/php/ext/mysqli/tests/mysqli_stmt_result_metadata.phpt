--TEST--
mysqli_stmt_result_metadata()
--SKIPIF--
<?php
require_once('skipif.inc');
require_once('skipifemb.inc');
require_once('skipifconnectfailure.inc');
?>
--FILE--
<?php
	require_once("connect.inc");

	$tmp    = NULL;
	$link   = NULL;

	if (!is_null($tmp = @mysqli_stmt_result_metadata()))
		printf("[001] Expecting NULL, got %s/%s\n", gettype($tmp), $tmp);

	if (!is_null($tmp = @mysqli_stmt_result_metadata($link)))
		printf("[002] Expecting NULL, got %s/%s\n", gettype($tmp), $tmp);

	require('table.inc');

	if (!$stmt = mysqli_stmt_init($link))
		printf("[003] [%d] %s\n", mysqli_errno($link), mysqli_error($link));

	if (NULL !== ($tmp = mysqli_stmt_result_metadata($stmt)))
		printf("[004] Expecting NULL, got %s/%s\n", gettype($tmp), $tmp);

	if (!mysqli_stmt_prepare($stmt, "SELECT id, label FROM test"))
		printf("[005] [%d] %s\n", mysqli_stmt_errno($stmt), mysqli_stmt_error($stmt));

	if (!is_object(($res = mysqli_stmt_result_metadata($stmt))))
		printf("[006] Expecting object, got %s/%s\n", gettype($tmp), $tmp);

	if (2 !== ($tmp = mysqli_num_fields($res)))
		printf("[007] Expecting int/2, got %s/%s, [%d] %s\n",
			gettype($tmp), $tmp, mysqli_errno($link), mysqli_error($link));

	if (!is_object($field0_fetch = mysqli_fetch_field($res)))
		printf("[008] Expecting object, got %s/%s, [%d] %s\n",
			gettype($field0_fetch), $field0_fetch, mysqli_errno($link), mysqli_error($link));

	if (!is_object($field0_direct = mysqli_fetch_field_direct($res, 0)))
		printf("[009] Expecting object, got %s/%s, [%d] %s\n",
			gettype($field0_direct), $field0_direct, mysqli_errno($link), mysqli_error($link));

	if ($field0_fetch != $field0_direct) {
		printf("[010] mysqli_fetch_field() differs from mysqli_fetch_field_direct()\n");
		var_dump($field0_fetch);
		var_dump($field0_direct);
	}

	var_dump($field0_fetch);

	if (!is_array($tmp = mysqli_fetch_fields($res)))
		printf("[011] Expecting array, got %s/%s, [%d] %s\n",
			gettype($tmp), $tmp, mysqli_errno($link), mysqli_error($link));

	if (empty($tmp[0]) || empty($tmp[1]) || $tmp[0] != $field0_direct) {
		printf("[012] mysqli_fetch_fields() return value is suspicious\n");
		var_dump($tmp);
	}

	if (!mysqli_field_seek($res, 1))
		printf("[013] [%d] %s\n", mysqli_errno($link), mysqli_error($link));

	if (!is_object($field1_direct = mysqli_fetch_field_direct($res, 1)))
		printf("[014] Expecting object, got %s/%s, [%d] %s\n",
			gettype($field1_direct), $field1_direct, mysqli_errno($link), mysqli_error($link));

	if ($tmp[1] != $field1_direct) {
		printf("[015] mysqli_fetch_field_direct() differs from mysqli_fetch_fields()\n");
		var_dump($field1_direct);
		var_dump($tmp);
	}

	if (1 !== ($tmp = mysqli_field_tell($res)))
		printf("[016] Expecting int/1, got %s/%s, [%d] %s\n",
			gettype($tmp), $tmp, mysqli_errno($link), mysqli_error($link));

	mysqli_free_result($res);
	mysqli_stmt_close($stmt);

	if (NULL !== ($tmp = mysqli_stmt_result_metadata($stmt)))
		printf("[017] Expecting NULL, got %s/%s\n");

	/* Check that the function alias exists. It's a deprecated function,
	but we have not announce the removal so far, therefore we need to check for it */
	if (!is_null($tmp = @mysqli_stmt_result_metadata()))
		printf("[018] Expecting NULL, got %s/%s\n", gettype($tmp), $tmp);

	mysqli_close($link);
	print "done!";
?>
--CLEAN--
<?php
	require_once("clean_table.inc");
?>
--EXPECTF--

Warning: mysqli_stmt_result_metadata(): invalid object or resource mysqli_stmt
 in %s on line %d
object(stdClass)#5 (13) {
  [%u|b%"name"]=>
  %unicode|string%(2) "id"
  [%u|b%"orgname"]=>
  %unicode|string%(2) "id"
  [%u|b%"table"]=>
  %unicode|string%(4) "test"
  [%u|b%"orgtable"]=>
  %unicode|string%(4) "test"
  [%u|b%"def"]=>
  %unicode|string%(0) ""
  [%u|b%"db"]=>
  %unicode|string%(%d) "%s"
  [%u|b%"catalog"]=>
  %unicode|string%(%d) "%s"
  [%u|b%"max_length"]=>
  int(0)
  [%u|b%"length"]=>
  int(11)
  [%u|b%"charsetnr"]=>
  int(63)
  [%u|b%"flags"]=>
  int(49155)
  [%u|b%"type"]=>
  int(3)
  [%u|b%"decimals"]=>
  int(0)
}

Warning: mysqli_stmt_result_metadata(): Couldn't fetch mysqli_stmt in %s on line %d
done!