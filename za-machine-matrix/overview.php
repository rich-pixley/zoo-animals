<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1" />
<link href="../za-base/za.css" rel="stylesheet" type="text/css" />
<?php require "../za-base/za-headers.php"; ?>
<?php require "mm-headerbar.php"; ?>
<?php require "/net/nova-builder.palm.com/var/www/za-animals.php"; ?>

<title><?=$hostname;?> Machine Matrix</title>

</head>
<body>
<?= headers("machine matrix", gen_mmthirdbar("overview")); ?>
<br />

<div class="content">
<h1>Current Zoo Animals</h1>

<table border="1">

<thead>
<tr>
<th rowspan="2">machine</th>
<th rowspan="2">OS</th>
<th colspan="2"><a href="http://wiki.palm.com/display/Nova/Nova+Continuous+Builders">continuous builder</a></th>
<th colspan="2"><a href="http://wiki.palm.com/display/Nova/Nova+Dependency+Checker">dependency checker</a></th>
<th colspan="2"><a href="http://wiki.palm.com/display/Nova/Nova+Submission+Checker">submission checker</a></th>
</tr>
<tr>
<th>targets</th>
<th>branch</th>
<th>targets</th>
<th>branch</th>
<th>targets</th>
<th>branch</th>
</tr>
</thead>

<tbody>


<?php
   foreach ($animals as $za) {
	$f = "/net/$za.palm.com/etc/lsb-release";
  	if (!file_exists($f)) {
		echo '<tr class="unavailable">';
  	} else {
		$gf = fopen("/net/$za.palm.com/etc/apt/sources.list", "r");
		$gline = fgets($gf);
		fclose($gf);

		if (strpos($gline, "unstable")) {
			echo '<tr class="unstable">';

		} else if (strpos($gline, "testing")) {
			echo '<tr class="testing">';

		} else if (strpos($gline, "stable")) {
			echo '<tr class="stable">';

		} else {
	   		echo '<tr class="unavailable">';
		}
   	}

	echo "<td><a href=\"https://", $za, ".palm.com\">", $za, ".palm.com</a></td>\n";

	echo "<td>";
	if (file_exists($f)) {
		echo htmlspecialchars(trim(`sed -n -e '/DISTRIB_DESCRIPTION="/s///' -e '/"$/s///p' < /net/$za.palm.com/etc/lsb-release`));
	}
    	echo "</td>\n";


	$f = "/net/$za.palm.com/home/za-cb/workdir/configargs";
	echo "<td>";
  	if (file_exists($f)) {
  		echo "<a href=\"https://$za.palm.com/za-continuous-builder\">";
      		echo tabbrev(htmlspecialchars(trim(file_get_contents($f)))), "</a>";
  	}
    	echo "</td>\n";

	$svnloc = "/net/$za.palm.com/home/za-cb/workdir/svnloc";
	echo "<td>";
  	if (file_exists($svnloc)) {
  		echo "<a href=\"https://$za.palm.com/za-continuous-builder\">";
      		echo babbrev(htmlspecialchars(trim(file_get_contents($svnloc)))), "</a>";
  	}
    	echo "</td>\n";


	$f = "/net/$za.palm.com/home/za-dc/workdir/targetlist";
	echo "<td>";
  	if (file_exists($f)) {
  		echo "<a href=\"https://$za.palm.com/za-dependency-checker\">";
      		echo tabbrev(htmlspecialchars(trim(file_get_contents($f)))), "</a>";
  	}
    	echo "</td>\n";

	$svnloc = "/net/$za.palm.com/home/za-dc/workdir/svnloc";
	echo "<td>";
  	if (file_exists($svnloc)) {
  		echo "<a href=\"https://$za.palm.com/za-dependency-checker\">";
      		echo babbrev(htmlspecialchars(trim(file_get_contents($svnloc)))), "</a>";
  	}
    	echo "</td>\n";


	$f = "/net/$za.palm.com/home/za-sc/workdir/configargs";
	echo "<td>";
  	if (file_exists($f)) {
  		echo "<a href=\"https://$za.palm.com/za-submission-checker\">";
      		echo tabbrev(htmlspecialchars(trim(file_get_contents($f)))), "</a>";
  	}
    	echo "</td>\n";

	$svnloc = "/net/$za.palm.com/home/za-sc/workdir/svnloc";
	echo "<td>";
  	if (file_exists($svnloc)) {
  		echo "<a href=\"https://$za.palm.com/za-submission-checker\">";
      		echo babbrev(htmlspecialchars(trim(file_get_contents($svnloc)))), "</a>";
  	}
    	echo "</td>\n";

	echo "</tr>\n";
   }

?>

</tbody>

</table>
</div>

<br />
<div>
Color codes represent package repositories: red - unstable, yellow -
testing, blue - stable.  Unavailable machines are represented in italics.
</div>

<?= footer() ?>
</body>
</html>
