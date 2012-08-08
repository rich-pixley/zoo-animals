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
<title><?= $hostname;?> Submission Checker Configs</title>
</head>
<body>
<?= headers("submission checker", gen_prethirdbar("configs")); ?>

<div class="content">
<h1>Configs <?= file_exists("FAILING") ? "<font color=\"red\"><b>FAILING!</b></font>" : "" ?> </h1>

<table border="0">
<tr><td>
Checking against:

<?= "\"" . $svnloc . "/" . $bomloc . "\""; ?>
<br>
<?= "\"" . $svnbomloc . "\""; ?>

<br><br>
<table border="1">
<tr><td>

<?= (file_exists($disablefile) || file_exists($disableapplicationfile))
    ? "<h2>DISABLED</h2>" : "" ; ?>

configures:

<?= file_exists($configargsfile)
    ? "\"" . htmlspecialchars(trim(file_get_contents($configargsfile))) . "\""
    : "default" ?>

<br>checks:

<?= file_exists($checktargetfile)
    ? "\"" . htmlspecialchars(trim(file_get_contents($checktargetfile))) . "\""
    : "default"; ?>

<br>lowwater:

<?= file_exists($lowwaterfile)
    ? "\"" . htmlspecialchars(trim(file_get_contents($lowwaterfile))) . "\""
    : "default"; ?>

<br>highwater:

<?= file_exists($highwaterfile)
    ? "\"" . htmlspecialchars(trim(file_get_contents($highwaterfile))) . "\""
    : "default"; ?>

<?php
    if (file_exists($allfullbuildsfile)) {
	echo "<br><b>all-full-builds</b>";
    }

    if (file_exists($backtobackfile)) {
        echo "<br><b>back-to-back</b>";
    }
?>

</td><td>
Checker is
<?= file_exists($lockfile) ? "Running" : "not running" ; ?><br>
<a href="za-submission-checker-form">new submission</a>
<p>
</td></tr>
</table>
</div>

<?= footer(); ?>
</body>
</html>
