<?php
include 'lib.php';
$result = getUsers();

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>User App</title>
    <link href="style/style.css" rel="stylesheet">
</head>
<body>
<div class="page">
    <div class="wrap">
    <div class="header">
        Пользователи
    </div>
    <div class="table">
        <form action="delete.php" method="POST">
            <table>
                <?php
                createTable($result);
                ?>
            </table>
            <button type="submit">Удалить</button>
        </form>

    </div>
    <div class="newUser">
        <form action="add.php" method="post">
            <table>
                <tr>
                    <td>email</td>
                    <td><input type="text" name="email" /></td>
                    <td>login</td>
                    <td><input type="text" name="name" /></td>
                </tr>
            </table>
            <button type="submit">Добавить</button>
        </form>
    </div>
    </div>
</div>
</body>
</html>
