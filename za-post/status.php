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
<title><?=$hostname;?> Dependency Checker Status</title>
</head>
<body>
<?= headers("post-commit checker", gen_postthirdbar("status")); ?>

<div class="content">
<h1>Status</h1>
<table border="0">
<tr><td>
Checking from:

<?= htmlspecialchars(trim(`$conftool -k svnloc`)); ?>

<br><br>
<table border="1">
<tr><td>

<table>
<tr><td colspan="2">
<?= (file_exists(${disablefile}) || file_exists(${disableapplicationfile}))
    ? "<h2>DISABLED</h2>" : "" ; ?>
</td>
</tr>

<tr>
<td>configures:</td>
<td><?= htmlspecialchars(trim(`$conftool -k configargs`)) ?></td>
</tr>

<tr>
<td>targets:</td>
<td><?= htmlspecialchars(trim(`$conftool -k targetlist`)) ?></td>
</tr>

<tr>
<td>mail to owners:</td>
<td><?= htmlspecialchars(trim(`$conftool -k mail-to-owners`)) ?></td>
</tr>
</table>
<br>

<table>
<tr><td><?php
	$handle = popen("ls -d " . $attempts . "/* | wc -l", "r");
	$covered = stream_get_contents($handle);
	echo $covered;
?></td>
<td>covered</td>
<td>100%</td>
</tr>

<tr><td><?php
	$handle = popen("ls -d " . $attempts . "/*/new | wc -l", "r");
	$new = stream_get_contents($handle);
	echo $new;
?></td>
<td>new</td>
<td><?= round((100 * $new) / $covered); ?>%</td>
</tr>

<tr><td><?php
	$handle = popen("ls -d " . $attempts . "/*/bumped | wc -l", "r");
	$bumped = stream_get_contents($handle);
	echo $bumped;
?></td>
<td>bumped</td>
<td><?= round(($bumped * 100) / $covered); ?>%</td>
</tr>

<tr><td><?php
	$handle = popen("grep built " . $attempts . "/*/status | wc -l", "r");
	$built = stream_get_contents($handle);
	echo $built;
?></td>
<td>built</td>
<td><?= round(($built * 100) / $covered); ?>%</td>
</tr>

<tr><td><?php
	$handle = popen("grep skipped " . $attempts . "/*/status | wc -l", "r");
	$skipped = stream_get_contents($handle);
	echo $skipped;
?></td>
<td>skipped</td>
<td><?= round(($skipped * 100) / $covered); ?>%</td>
</tr>

<tr><td><?php
	$handle = popen("grep notargetarch " . $attempts . "/*/status | wc -l", "r");
	$notargetarch = stream_get_contents($handle);
	echo $notargetarch;
?></td>
<td>notargetarch</td>
<td><?= round(($notargetarch * 100) / $covered); ?>%</td>
</tr>

<tr><td><?php
	$handle = popen("grep failed " . $attempts . "/*/status | wc -l", "r");
	$failed = stream_get_contents($handle);
	echo $failed;
?></td>
<td>failed</td>
<td><?= round(($failed * 100) / $covered); ?>%</td>
</tr>

</table>

</td><td>
<h2>Channels:</h2>

<table border="1">
<thead>
<tr>
  <th>Channel</th>
  <th>Pid</th>
  <th>Status</th>
</tr>
</thead>

<?php
$builders = ${workdir} . "/builders";

if (file_exists(${builders})) {
	foreach (scandir(${builders}, "0") as ${channel}) {
		if (${channel} != "." && ${channel} != ".." && ${channel} != ".svn") {
			echo "<tr>";
			echo "<td><a href=\"../za-php-utils/cat.php?file=" . ${builders} . "/" . ${channel} . "/log\">" . ${channel} . "</a></td>\n";

			$p = htmlspecialchars(trim(file_get_contents(${workdir} . "/" . ${channel} . ".LOCK")));
			if ($p != "") {
				if (`ps h -p $p` != "") {
					echo "<td>$p</td>\n";

					$s = "${builders}/${channel}/status";
					echo "<td>" . (file_exists($s)
						? htmlspecialchars(trim(file_get_contents($s))) : "unknown") . "</td>\n";
				} else {
					echo "<td>down</td>\n";
					echo "<td>down</td>\n";
				}
			} else {
				echo "<td>down</td>\n";
				echo "<td>down</td>\n";
			}
		}
	}
}
?>
</table>

</td></tr>
</table>

<?= footer(); ?>
</body>
</html>
