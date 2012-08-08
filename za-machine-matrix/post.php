<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1" />
<link href="../za-base/za.css" rel="stylesheet" type="text/css" />
<?php require "../za-base/za-headers.php"; ?>
<?php require "mm-headerbar.php"; ?>
<?php require "/net/nova-builder.palm.com/var/www/za-animals.php"; ?>
<title><?=$hostname;?> Dependency Checkers</title>
</head>
<body>
<?= headers("machine matrix", gen_mmthirdbar("dependency checkers")); ?>
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
	<th>targets</th>
	<th>covered</th>
	<th>errors</th>

	<th>channel</th>
	<th>pid</th>
	<th>status</th>
</tr>
</thead>
<tbody>
<?php
$workdir = "/home/za-dc/workdir";

foreach ($animals as $machine) {
	$myworkdir["http"] = "https://$machine.palm.com";
	$myworkdir["base"] = "/net/$machine.palm.com";
	$myworkdir["local"] = $myworkdir["base"] . ${workdir};

	$available = file_exists($myworkdir["local"]);
	if (!$available)
		continue;

	echo "<tr>";

	if (file_exists($myworkdir["local"])) {
		$builder_count = -1;
		$builders = $myworkdir['local'] . '/builders';
		foreach (scandir($builders, "0") as ${channel}) {
			$builder_count += 1;
		}

		echo "<td rowspan=\"$builder_count\"><a href=\"";
		echo $myworkdir["http"];
		echo "\">$machine.palm.com</a></td>\n";

		echo "<td rowspan=\"$builder_count\">";
		echo htmlspecialchars(trim(`sed -n -e '/DISTRIB_DESCRIPTION="/s///' -e '/"$/s///p' < /net/$machine.palm.com/etc/lsb-release`));
		echo "</td>\n";

		echo "<td rowspan=\"" . $builder_count . "\">";
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

		echo "</td>\n";



		echo "<td rowspan=\"" . $builder_count . "\">"
			. babbrev(suckfile($myworkdir["local"] . "/svnloc")) . "</td>\n";

		echo "<td rowspan=\"" . $builder_count . "\">"
			. tabbrev(suckfile($myworkdir["local"] . "/targetlist")) . "</td>\n";

		echo "<td rowspan=\"" . $builder_count . "\">";
		$handle = popen("ls -d " . $myworkdir["local"] . "/attempts/* | wc -l", "r");
		echo stream_get_contents($handle) . "</td>\n";

		echo "<td rowspan=\"" . $builder_count . "\">";
		$handle = popen("grep failed " . $myworkdir["local"] . "/attempts/*/status | wc -l", "r");
		echo stream_get_contents($handle) . "</td>\n";

		foreach (scandir($builders, "0") as $channel) {
			if (${channel} != "." && ${channel} != ".." && ${channel} != ".svn") {
				echo "<td><a href=\"../php-utils/cat.php?file=" . ${builders} . "/" . ${channel} . "/log\">"
					. ${channel} . "</a></td>\n";

				$pidfile = "${builders}/${channel}/LOCK";
				if (file_exists($pidfile)) {
					$p = htmlspecialchars(trim(file_get_contents($pidfile)));

					echo "<td>$p</td>\n";
					$s = "${builders}/${channel}/status";
					echo "<td>" . (file_exists($s) ? htmlspecialchars(file_get_contents($s)) : "unknown") . "</td>\n";

				} else {
					echo "<td>down</td>\n";
					echo "<td>down</td>\n";
				}
			}
			echo "</tr>\n";
		}

	} else {
		echo "<td><a href=\"" . $myworkdir["http"] . "\">" . $machine . ".palm.com</a></td>\n";
		echo "<td colspan=\"7\" class=\"unavailable\">unavailable</td></tr>";
	}
}

?>

</tbody>
</table>
</div>

<?= footer(); ?>

</body>
</html>
