<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1" />
<link href="../za-base/za.css" rel="stylesheet" type="text/css" />
<?php include "../za-base/za-headers.php"; $workdir = "/home"; ?>
<title><?=$hostname;?> Machine Info</title>
</head>

<body>
<?= headers("info", array()); ?>
<br />
<h1>Machine Info</h1>

<div class="content">

<h2>Summary</h2>
<table border=3>
<tr>
  <td>cpu count</td>
  <td><?= htmlspecialchars(`grep processor /proc/cpuinfo | wc -l`) ?></td>
</tr>
<tr>
  <td>cpu MHz</td>
  <td><?= htmlspecialchars(`awk '/cpu MHz/ { print $4; exit; }' /proc/cpuinfo`) ?></td>
</tr>
<tr>
  <td>bogomips</td>
  <td><?= htmlspecialchars(`awk '/bogomips/ { print $3; exit; }' /proc/cpuinfo`) ?></td>
</tr>
<tr>
  <td>memory</td>
  <td><?= htmlspecialchars(`awk '/MemTotal/ { print $2, $3; exit; }' /proc/meminfo`) ?></td>
</tr>
<tr>
  <td>available disk</td>
  <td><?= htmlspecialchars(`df -h ${workdir} | awk 'NR == 2 { print $4; }'`) ?></td>
</tr>
</table>
</div>

<div class="content">
<h2>Desciption</h2><?= htmlspecialchars(file_exists("../za-machine-description")
		       ? file_get_contents("../za-machine-description")
		       : "no description available"); ?>
</div>

<div class="content">
<h2>lsb_release -a</h2><pre><?= htmlspecialchars(`lsb_release -a`); ?></pre>

</div><div class="content">
<h2>uptime</h2><pre><?= htmlspecialchars(`uptime`); ?></pre>

</div><div class="content">
<h2>df -k</h2><pre><?= htmlspecialchars(`df -k`); ?></pre>

</div><div class="content">
<h2>/proc/cpuinfo</h2>
<pre><?= htmlspecialchars(file_get_contents("/proc/cpuinfo")); ?></pre>

</div><div class="content">
<h2>/proc/meminfo</h2>
<pre><?= htmlspecialchars(file_get_contents("/proc/meminfo")); ?></pre>

<?php
   $cronfile = "/etc/cron.d/za-continuous-builder";

   if (file_exists($cronfile)) {
   	echo '</div><div class="content">';
   	echo '<h2>', $cronfile, '</h2>';
   	echo '<pre>', htmlspecialchars(file_get_contents($cronfile)), '</pre>';
   }?>

<?php
   $cronfile = "/etc/cron.d/za-dependency-checker";

   if (file_exists($cronfile)) {
   	echo '</div><div class="content">';
   	echo '<h2>', $cronfile, '</h2>';
   	echo '<pre>', htmlspecialchars(file_get_contents($cronfile)), '</pre>';
   }?>

<?php
   $cronfile = "/etc/cron.d/za-submission-checker";

   if (file_exists($cronfile)) {
   	echo '</div><div class="content">';
   	echo '<h2>', $cronfile, '</h2>';
   	echo '<pre>', htmlspecialchars(file_get_contents($cronfile)), '</pre>';
   }?>

