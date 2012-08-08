<!--
Copyright (c) 2008 - 2012 Hewlett-Packard Development Company, L.P.

Licensed under the Apache License, Version 2.0 (the "License"); you
may not use this file except in compliance with the License.  You may
obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.  See the License for the specific language governing
permissions and limitations under the License.
-->

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1" />
<link href="../za-base/za.css" rel="stylesheet" type="text/css" />
<?php require "../za-base/za-headers.php"; ?>
<?php require "pre-headerbar.php"; ?>
<title><?= $hostname;?> Submission Checker Status</title>
</head>
<body>
<?= headers("submission checker", gen_prethirdbar("status")); ?>

<div class="content">
<h1>Status for <?= $svnloc ?></h1>

<table border="1">
<thead>
<tr>
	<th>Pass</th>
	<th>Revision</th>
	<th>Type</th>
	<th>Basis</th>
	<th>Status</th>

	<th>Request</th>

	<th>Validation</th>
	<th>Requester</th>
	<th>Notes</th>
	<th>Log/Tail</th>
</tr>
</thead>

<tbody>
<?php
$passesdir = "$workdir/passes";
$results = "$workdir/results";

$descriptorspec = array(
   0 => array("pipe", "r"),  // stdin is a pipe that the child will read from
   1 => array("pipe", "w"),  // stdout is a pipe that the child will write to
   2 => array("pipe", "w"),  // stderr is a pipe that the child will write to
);

$workqueue = "/usr/bin/sudo -u $preowner -H $mylibexecdir/WorkQueue";

$process = proc_open($workqueue . " --just-keys",
	$descriptorspec, $pipes);

fclose($pipes[0]);

if (is_resource($process)) {
	while (($a = trim(fgets($pipes[1]))) != FALSE) {

		$inprocess = False;

		foreach (scandir($passesdir, "1") as $pass) {
			$request = $passesdir . "/" . $pass . "/request";

			if (file_exists($request)
				&& (trim(file_get_contents($request)) == $a)) {
				$inprocess = True;
				break;
			}
		}

		if (!$inprocess) {
			echo "<tr>\n";
			echo "<td></td>\n";
			echo "<td></td>\n";
			echo "<td></td>\n";
			echo "<td></td>\n";
	   		echo "<td>queued</td>\n";
	   		echo "<td>$a</td>\n";

	   		echo "<td>" . htmlspecialchars(trim(shell_exec($workqueue . " --print-validation " . $a))) . "</td>\n";
	   		echo "<td>" . htmlspecialchars(trim(shell_exec($workqueue . " --print-requester " . $a))) . "</td>\n";
	   		echo "<td>" . htmlspecialchars(trim(shell_exec($workqueue . " --print-releasenotes " . $a))) . "</td>\n";

	   		echo "<td></td>\n";
			echo "</tr>\n";
		}
	}
}

fclose($pipes[1]);
fclose($pipes[2]);
$return_value = proc_close($process);

if (file_exists($passesdir)) {
	foreach (scandir($passesdir, "1") as $a) {
		if ($a != "." && $a != ".." && $a != ".svn") {
			$statusfile = $passesdir . "/" . $a . "/status";
			if (!file_exists($statusfile)) {
				$cls = "unknown";
			} else {
				$status = htmlspecialchars(trim(file_get_contents($statusfile)));

				if ($status == "built"
					|| $status == "failed"
					|| $status == "interrupted"
					|| $status == "cleared"
					|| $status == "redundant speculation") {
					$cls = $status;
				} elseif (strpos($status, "committed") !== FALSE) {
					$cls = "committed";
				} elseif (strpos($status, "failed") !== FALSE) {
					$cls = "failed";
				} else {
					$cls = "unknown";
				}
			}
			echo "<tr class=\"" . $cls . "\">\n";

			$snapshot = "$fsmountpoint/$preowner-$a";
			$partial = substr($workdir, strlen($fsmountpoint), strlen($workdir));
			$hookscript = trim(`$conftool -s za-pre -k hookscript`);
			$final = trim(`$hookscript builddirname`);

			if (file_exists("$fsmountpoint/$preowner-$a/$partial/$final")) {
				echo "<td><a href=\"https://$hostname/$preowner-$a\">$a</a></td>\n";
			} else {
				echo "<td>$a</td>\n";
			}

			echo "<td>";
			$revision = $passesdir . "/" . $a . "/revision";
			$n = rtrim(htmlspecialchars(file_exists($revision) ? trim(file_get_contents($revision)) : "unknown"));
   			echo ($n == "") ? "" : $n;
			echo "</td>\n";

			$buildtype = "$passesdir/$a/buildtype";
			echo "<td>" . htmlspecialchars(file_exists($buildtype)
				? trim(file_get_contents($buildtype))
				: "unknown");
			echo "</td>";

			$basisfile = "$passesdir/$a/basis";
			echo "<td>" . htmlspecialchars(file_exists($basisfile)
				? trim(file_get_contents($basisfile))
				: "unknown");
			echo "</td>";

			echo "<td>$status</td>\n";

			$requestfile = "$passesdir/$a/request";
			echo "<td>" . htmlspecialchars(file_exists($requestfile)
				? trim(file_get_contents($requestfile))
				: "");
			echo "</td>";

			$validation = "$passesdir/$a/validation";
			echo "<td>" . htmlspecialchars(file_exists($validation)
				? trim(file_get_contents($validation))
				: "");
			echo "</td>\n";

			$requester = "$passesdir/$a/requester";
			echo "<td>" . htmlspecialchars(file_exists($requester)
				? trim(file_get_contents($requester))
				: "unknown");
			echo "</td><td>\n";

			$notes = $passesdir . "/" . $a . "/notes";
			$n = rtrim(htmlspecialchars(file_exists($notes) ? trim(file_get_contents($notes)) : "unknown"));
   			echo ($n == "") ? "" : $n;
			echo "</td><td>\n";

   			$l = $passesdir . "/" . $a . "/log";
			echo file_exists($l)
   				? "<a href=\"../za-php-utils/cat?file=$passesdir/$a/log\">log</a>/<a href=\"../za-php-utils/tail?file=$passesdir/$a/log\">tail</a>"
				: "&nbsp";

			echo "</td></tr>";
		}
	}
}
?>
</tbody>
</table>
</div>

<?= footer(); ?>
</body>
</html>
