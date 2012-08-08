<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1" />
<link href="../za-base/za.css" rel="stylesheet" type="text/css" />
<?php require "../za-base/za-headers.php"; ?>
<?php if (isset($_GET['file'])) {
   $filename = $_GET['file'];
   $handle = popen("tail -200 " . $filename, "r");
}?>
  <title><?= $filename; ?></title>
</head>
<body>
<?= headers("none", array()); ?>

<div class="content">
<h1><?= $filename; ?></h1>
<pre>
<?= isset($_GET['file'])
    ? htmlspecialchars(stream_get_contents($handle))
    : "" ; ?>
</pre>
</div>

<?= footer(); ?>
</body>
</html>
