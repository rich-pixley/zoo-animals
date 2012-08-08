<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1" />
<link href="../za-base/za.css" rel="stylesheet" type="text/css" />
<?php require "../za-base/za-headers.php"; ?>
<?php require "mm-headerbar.php"; ?>
<?php require "/net/nova-builder.palm.com/var/www/za-animals.php"; ?>
<title><?=$hostname;?> Submission Checkers</title>
</head>
<body>
<?= headers("machine matrix", gen_mmthirdbar("submission checkers")); ?>
<br />

<div class="content">

<h1>Current Status</h1>

<table border="1">
<thead>
<tr>
	<th>name</th>
	<th>OS</th>
	<th>repository</th>
	<th>branch</th>
	<th>configures</th>
	<th>targets</th>
</tr>
</thead>
<tbody>
<?php
$workdir = "/home/za-sc/workdir";

foreach ($animals as $machine) {
	$myworkdir["http"] = "https://" . $machine . ".palm.com";
	$myworkdir["base"] = "/net/" . $machine . ".palm.com";
	$myworkdir["local"] = $myworkdir["base"] . ${workdir};

	$available = file_exists($myworkdir["local"]);
	if (!$available)
		continue;

	echo "<tr>";

	if (file_exists($myworkdir["local"])) {
		echo "<td><a href=\"" . $myworkdir["http"] . "\">" . $machine . ".palm.com</a></td>\n";

		echo "<td>";
		echo htmlspecialchars(trim(`sed -n -e '/DISTRIB_DESCRIPTION="/s///' -e '/"$/s///p' < /net/$machine.palm.com/etc/lsb-release`));
		echo "</td>\n";

		echo "<td>";
		$gf = fopen($myworkdir["base"] . "/etc/apt/sources.list", "r");
		$gline = fgets($gf);
		fclose($gf);

		if (strpos($gline, "unstable")) {
			echo 'unstable';

		} else if (strpos($gline, "testing")) {
			echo 'testing';

		} else if (strpos($gline, "stable")) {
			echo 'stable';

		}
		echo "</td>";

		echo "<td>" . babbrev(suckfile($myworkdir["local"] . "/svnloc")) . "</td>\n";
		echo "<td>" . suckfile($myworkdir["local"] . "/configargs") . "</td>\n";
		echo "<td>" . suckfile($myworkdir["local"] . "/checktargets") . "</td>\n";

	} else {
		echo "<td><a href=\"" . $myworkdir["http"] . "\">" . $machine . ".palm.com</a></td>\n";
		echo "<td colspan=\"7\" class=\"unavailable\">unavailable</td></tr>";
	}
	echo "</tr>";
}

?>
</tbody>
</table>
</div>

<?= footer(); ?>

</body>
</html>
