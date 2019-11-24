<?php
$handle = fopen("my.tif", 'rb');
$img = new Imagick();
$img->readImageFile($handle);
?>
