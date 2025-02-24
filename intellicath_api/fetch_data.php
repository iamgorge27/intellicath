<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");

$servername = "localhost";
$username = "root"; 
$password = ""; 
$dbname = "intellicath";

$conn = new mysqli($servername, $username, $password, $dbname);
if ($conn->connect_error) {
    die(json_encode(["status" => "error", "message" => "Database connection failed"]));
}

$sql = "SELECT * FROM intellicath_data ORDER BY id DESC LIMIT 1"; 
$result = $conn->query($sql);

if ($result->num_rows > 0) {
    $row = $result->fetch_assoc();
    echo json_encode($row);
} else {
    echo json_encode(["status" => "error", "message" => "No data found"]);
}

$conn->close();
?>
