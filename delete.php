<?php
include ("lib.php");
$del = $_POST['del'];
if (!empty($del)) {
    $ids = [];
    for($i=0;$i<count($del);$i++)
    {
        $ids[$i]= $del[$i];
    }
    $result = deleteUsers($ids);

    if ($result) {
        header("Location: index.php?del_success=1");
    } else {
        header("Location: index.php?del_error=1");
    }
} else {
    echo "Не переданы параметры";
}