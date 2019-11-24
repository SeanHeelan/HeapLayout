<?php
putenv("SSR_ENABLE_ALLOCATION_TRACKING=1");
$zip = new ZipArchive();
if ($zip->open("/data/Documents/git/php-shrike/bug_triggers/cve_2016_3078_zip_getfromindex/trigger.zip") !== TRUE) {
    echo "cannot open archive\n";
} else {
    for ($i = 0; $i < $zip->numFiles; $i++) {
        $data = $zip->getFromIndex($i);
    }
    $zip->close();
}
?>
