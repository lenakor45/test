<?php
$link = mysqli_connect("localhost", "root", "", "user");
function getUsers(){
    if (!$GLOBALS['link']) {
        echo 'Не могу соединиться с БД. Код ошибки: ' . mysqli_connect_errno() . ', ошибка: ' . mysqli_connect_error();
        exit;
    }
    $select = "SELECT * FROM user.user;";
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
        $query ="UPDATE user.user SET IsDel='1' WHERE id='".$ids[$i]."'";
        mysqli_query($GLOBALS['link'], $query);
    }
    return true;
}

function addUser($newUser)
{
    $user = getUsers();
    $email=[];$login=[];
    for($i=0;$i<mysqli_num_rows($user);$i++)
    {
        $row = mysqli_fetch_row($user);
        for ($j = 1 ; $j < 3 ; ++$j)
        {
            $email[$i] = $row[1];
            $login[$i] = $row[2];
        }

    }
    if(filter_var($newUser[0], FILTER_VALIDATE_EMAIL) && !in_array($newUser[0],$email) && !in_array($newUser[1],$login))
    {
        $query ="INSERT INTO user.user (email, login, IsDel) 
             VALUES('$newUser[0]','$newUser[1]','0')";
        mysqli_query($GLOBALS['link'], $query);
        return true;
    }
    else return false;

}