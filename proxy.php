<?php
$url = "http://professorxme.site/api.php?" . $_SERVER['QUERY_STRING'];
echo file_get_contents($url);
?>
