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
<?php require "post-headerbar.php"; ?>
<title><?=$hostname;?> Dependency Checker Results</title>
</head>
<body>
<?= headers("post-commit checker", gen_postthirdbar("results")); ?>

<?php
if ((count($_POST) + count($_GET)) > 0) {
	echo "<div class=\"content\"><table>\n";

	foreach ($_GET as $key => $value) {
	    echo "<tr><td>getvar " . $key . " as " . $value . "<td></tr>\n";
	}
	foreach ($_POST as $key => $value) {
		#echo "<tr><td>key</td><td>" . $key . "</td><td>value</td><td>" . $value . "</td></tr>";

		$x = explode("-", $value);
		$top = $x[0];
		unset($x[0]);
		$bottom = implode("-", $x);

		if ($top == "bump") {
			echo "<tr><td>bumping " . $bottom . `/usr/bin/sudo -u za-post -H /usr/bin/touch $attempts/$bottom/bumped` . "</td></tr>\n";
		}
	}
	echo "</table></div>\n";
}
?>

<div class="content">
<h1>Results</h1>
<form action="<?= $_SERVER['PHP_SELF'] ?>" method="post">
<button name="submit" type="submit">submit</button>
<button name="reset" type="reset">reset</button>

<table border="1">
<thead>
<tr>
	<th>Bump</th>
	<th>Component</th>
	<th>Status</th>
	<th>Last Checked</th>

	<th>reap</th>
	<th>co</th>
	<th>skipped</th>
	<th>notargetarch</th>
	<th>targetarch</th>
	<th>built</th>
	<th>done</th>

	<th>Target</th>
	<th>Image</th>
	<th>Owner</th>
	<th>Version</th>
	<th>Submission</th>
	<th>Log/Tail</th>
	<th>Log/Tail</th>
</tr>
</thead>

<?php
if (file_exists(${attempts})) {
	foreach (scandir(${attempts}, "0") as ${component}) {
		if (${component} != "." && ${component} != ".." && ${component} != ".svn") {
			$statusfile = ${attempts} . "/" . ${component} . "/status";
			$status = file_exists($statusfile) ? htmlspecialchars(trim(file_get_contents($statusfile))) : "unknown";

			if ($status == "unknown") {
				$class = " class=\"unknown\"";
			} else if ($status == "built" || $status == "skipped") {
				$class = "";
			} else {
				$class = " class=\"failed\"";
			}

			echo "<tr" . $class . ">";
			echo "<td><input "
				. " type=\"checkbox\" "
				. " name=\"bump-" . ${component} . "\""
				. " value=\"bump-" . ${component} . "\""
				. (file_exists("${attempts}/${component}/bumped") ? " disabled=true checked=\"checked\"" : "")
				. "</td>";

			echo "<td>${component}</td>";
			echo "<td>$status</td>";

			$last = "${attempts}/${component}/last";
			echo "<td>" . (file_exists($last) ? htmlspecialchars(trim(file_get_contents($last))) : "never") . "</td>";

   			$t = "${attempts}/${component}/timings";
			$start = `awk '$2 == "start" { print int($1); }' < $t`;
			$reap = `awk '$2 == "reap" { print int($1); }' < $t`;
			$co = `awk '$2 == "co" { print int($1); }' < $t`;
			$skipped = `awk '$2 == "skipped" { print int($1); }' < $t`;
			$targetarch = `awk '$2 == "targetarch" { print int($1); }' < $t`;
			$notargetarch = `awk '$2 == "notargetarch" { print int($1); }' < $t`;
			$built = `awk '$2 == "built" { print int($1); }' < $t`;
			$done = `awk '$2 == "done" { print int($1); }' < $t`;

			echo "<td>"
				. ($reap != "" ? hri($reap - $start) : "")
				. "</td>\n";
			echo "<td>"
				. ($co != "" ? hri($co - $reap) : "")
				. "</td>\n";
			echo "<td>"
				. ($skipped != "" ? hri($skipped - $co) : "")
				. "</td>\n";
			echo "<td>"
				. ($notargetarch != "" ? hri($notargetarch - $co) : "")
				. "</td>\n";
			echo "<td>"
				. ($targetarch != "" ? hri($targetarch - $co) : "")
				. "</td>\n";
			echo "<td>"
				. ($built != "" ? hri($built - $targetarch) : "")
				. "</td>\n";
			echo "<td>"
				. ($done != ""
					? ($built != ""
						? hri($done - $built)
						: ($notargetarch != ""
							? hri($done - $notargetarch)
							: ($skipped != ""
								? hri($done - $skipped)
								: "")))
					: "")
				. "</td>\n";

			$arch = ${attempts} . "/" . ${component} . "/targetarch";
			echo "<td>" . (file_exists($arch) ? htmlspecialchars(trim(file_get_contents($arch))) : "unknown") . "</td>";

			$image = ${attempts} . "/" . ${component} . "/image";
			echo "<td>" . (file_exists($image) ? htmlspecialchars(trim(file_get_contents($image))) : "unknown") . "</td>";

			$owner = ${attempts} . "/" . ${component} . "/owner";
   			$o = file_exists($owner) ? htmlspecialchars(trim(file_get_contents($owner))) : "unknown";
			echo "<td>" . ($o != '' ? ("<a href=\"mailto:" . $o . "\">" . $o . "</a>"): "&nbsp;") . "</td>";

			$version = ${attempts} . "/" . ${component} . "/version";
			echo "<td>" . (file_exists($version) ? htmlspecialchars(trim(file_get_contents($version))) : "unknown") . "</td>";

			$submission = ${attempts} . "/" . ${component} . "/submission";
			$s = file_exists($submission) ? htmlspecialchars(trim(file_get_contents($submission))) : "unknown";
			echo "<td>" . ($s != '' ? $s : "&nbsp;") . "</td>";

			$logsuccess = ${attempts} . "/" . ${component} . "/logsuccess";
			echo "<td>" . (file_exists($logsuccess) ? "<a href=\"../za-php-utils/cat?file=$logsuccess\">log</a>/<a href=\"../za-php-utils/tail?file=$logsuccess\">tail</a>"
				: "&nbsp") . "</td>";

			$loglast = ${attempts} . "/" . ${component} . "/loglast";
			echo "<td>" . (file_exists($loglast) ? "<a href=\"../za-php-utils/cat?file=$loglast\">log</a>/<a href=\"../za-php-utils/tail?file=$loglast\">tail</a>"
				: "&nbsp") . "</td>";

			echo "</tr>";

		}
	}
}
?>
</table>
<button name="submit" type="submit">submit</button>
<button name="reset" type="reset">reset</button>
</form>
</div>

<?= footer(); ?>
</body>
</html>
