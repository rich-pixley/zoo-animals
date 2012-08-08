<?php

$mmthirdbar = array("overview" => new headeritem("overview.php", "normal"),
	"pre commit checkers" => new headeritem("pre.php", "normal"),
	"post commit checkers" => new headeritem("post.php", "normal"));

function gen_mmthirdbar($highlight) {
	global $mmthirdbar;
	$mmthirdbar[$highlight]->status = "current";
	return $mmthirdbar;
}

function suckfile($file) {
	if (file_exists($file))
	   return htmlspecialchars(file_get_contents($file));
	else
	   return "<span style=\"font-style: italic\">unavailable</span>";
}

function tabbrev($in) {
   $in = trim($in);
   $e = explode(' ', $in);

   foreach ($e as $key => $value) {
   	if (strpos($value, '--enable-bb-number-threads') === 0) {
 		unset($e[$key]);
	}
    	if (strpos($value, '--enable-deterministic-buildinfo') === 0) {
		unset($e[$key]);
	}
    	if (strpos($value, '--enable-parallel-make') === 0) {
		unset($e[$key]);
	}
    	if (strpos($value, '--enable-fetch-to-workdir') === 0) {
		unset($e[$key]);
	}
    	if (strpos($value, '-D') === 0) {
		unset($e[$key]);
	}
   }

   $retval = implode(' ', $e);
   return $retval;
}

function babbrev($in) {
    $in = trim($in); 
    $patt = 'http://subversion.palm.com/main/nova/oe/'; 
    if (strpos($in, $patt) === 0) 
 	$in = substr($in, strlen($patt)); 
   return $in;
}

function dummy($in) {
	return $in;
}

?>
