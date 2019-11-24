<?php
$fp = bzopen("trigger.bz2", "r");
if ($fp === FALSE) {
    exit("ERROR: bzopen()");
}

$data = "";
while (!feof($fp)) {
    $res = bzread($fp);
    if ($res === FALSE) {
        exit("ERROR: bzread()");
    }
    $data .= $res;
}
bzclose($fp);
?>
