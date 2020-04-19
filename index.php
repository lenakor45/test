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
<!-- подключаем для работы Google Charts -->
<script type="text/javascript" src="https://www.google.com/jsapi"></script>
<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>

<div class="page">
    <div class="wrap">
        <?php
        if (!empty($_GET['del_success']))
        {
            echo('<h2>Удаление прошло!</h2>');
        }
        if(!empty($_GET['del_error']))
        {
            echo('<h2>Ошибка удаления</h2>');
        }
        if(!empty($_GET['add_success']))
        {
            echo('<h2>Пользователь добавлен</h2>');
        }
        if(!empty($_GET['add_error']))
        {
            echo('<h2>Ошибка добавления пользователя</h2>');
        }
        ?>
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
