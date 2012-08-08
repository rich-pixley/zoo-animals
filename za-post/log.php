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
<title><?=$hostname;?> Dependency Checker Log</title>
</head>
<body>
<?= headers("post-commit checker", gen_postthirdbar("log")); ?>

<div class="content">
<h1>Log</h1>

<div class="content">
<pre>
<?= file_exists(${logfile}) ? htmlspecialchars(trim(file_get_contents(${logfile}))) : ""; ?>
</pre>
</div>

<?= footer(); ?>
</body>
</html>
