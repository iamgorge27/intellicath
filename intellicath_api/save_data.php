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

$data = json_decode(file_get_contents("php://input"), true);
if (!$data) {
    echo json_encode(["status" => "error", "message" => "No data received"]);
    exit();
}

$urine_output = $data['urine_output'];
$urine_flow_rate = $data['urine_flow_rate'];
$catheter_bag_volume = $data['catheter_bag_volume'];
$remaining_volume = $data['remaining_volume'];
$predicted_time = $data['predicted_time'];
$actual_time = isset($data['actual_time']) ? $data['actual_time'] : null;  

$sql = "INSERT INTO intellicath_data (urine_output, urine_flow_rate, catheter_bag_volume, remaining_volume, predicted_time, actual_time) 
        VALUES (?, ?, ?, ?, ?, ?)";
$stmt = $conn->prepare($sql);
$stmt->bind_param("dddiis", 
    $urine_output, 
    $urine_flow_rate, 
    $catheter_bag_volume, 
    $remaining_volume, 
    $predicted_time,  
    $actual_time
);

if ($stmt->execute()) {
    echo json_encode(["status" => "success", "message" => "Data inserted successfully"]);
} else {
    echo json_encode(["status" => "error", "message" => "Error: " . $stmt->error]);
}

$stmt->close();
$conn->close();
?>
