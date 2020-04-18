<?php
include ("lib.php");
if ($_SERVER['REQUEST_METHOD'] === 'POST') {

    $newUser[0] = $_POST['email'];
    $newUser[1]=$_POST['name'];

    $result = addUser($newUser);

    if ($result) {
        header("Location: index.php?add_success=1");
    } else {
        header("Location: index.php?add_error=1");
    }
}