<?php
$link = mysqli_connect("localhost", "root", "", "user");
function getUsers(){
    if (!$GLOBALS['link']) {
        echo 'Не могу соединиться с БД. Код ошибки: ' . mysqli_connect_errno() . ', ошибка: ' . mysqli_connect_error();
        exit;
    }
    $select = "SELECT * FROM user.users;";
    $result = mysqli_query($GLOBALS["link"], $select);
    return $result;
}
function createTable($result)
{
    $rows = mysqli_num_rows($result);
    for($i=0;$i<$rows;++$i)
    {
        $row = mysqli_fetch_row($result);
        if ($row[3]=='0')
        {
            echo "<tr><td><input type='checkbox' name='del[]' value=$row[0]></td>";
            for ($j = 1 ; $j < 3 ; ++$j)
            {
                echo "<td>$row[$j]</td>";
            }
            echo "</tr>";
        }
    }
}

function deleteUsers($ids)
{
    for($i=0;$i<count($ids);$i++)
    {
        $query ="UPDATE user.users SET IsDel='1' WHERE id='".$ids[$i]."'";
        mysqli_query($GLOBALS['link'], $query);
    }
    return true;
}

function addUser($newUser)
{
    $query ="INSERT INTO user.users (email, login, IsDel) 
             VALUES('$newUser[0]','$newUser[1]','0')";
    mysqli_query($GLOBALS['link'], $query);
    return true;
}