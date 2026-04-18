<?php

require_once "ScyKernel.php";

$dir = "vines_images";
$path = $dir . "/php_vine.ppm";
$path2 = $dir . "/php_vine.png";
$testKey = "User";
$testValue = "Amanda";
$password = "ScyWeb_Global_Secret_2026";

// Ensure the local folder exists
if (!file_exists($dir)) {
    mkdir($dir, 0777, true);
}

// Instantiating 'scy' with the password and the local path
$scy = new ScyKernel($password, $path);

// Creating the test DBs
$scy->createPPM_DB($path);
$scy->syncPNG($path2, "load");

// Test both PPM and PNG DBs
$scy->putToPPM($testKey, $testValue, $password);
$scy->putToPNG($testKey, $testValue, $password);

// sync changes and refresh
$scy->syncPNG($path2, "commit");
$scy->syncPNG($path2, "load");

// Retrieve the results from both DBs
$result = $scy->getFromPPM($testKey, $password);
$result2 = $scy->getFromPNG($testKey, $password);

// Output Comparison
if ($result === $testValue && $result2 === $testValue) {
    $validationTest = $scy->validateDB($path) ? "Valid " : "Invalid";
    echo "✅ PHP KV Parity: SUCCESS (Recovered: " . $result . ")\n";
    echo "🧩 PPM is: " . $validationTest . "\n";
    $size = $scy->getFileSize($path2);
    $sizeStr = $size . " bytes";
    echo "📏 Size of Image DB: " . $sizeStr . "\n";
    // $scy->deleteDB($path);
    // $scy->deleteDB($path2);
    $parity_configs = [
        "C++" => "../cpp/vines_images/cpp_vine.png",
        "Go" => "../go/scykernel/vines_images/go_vine.png",
        "Java" => "../java/vines_images/java_vine.png",
        "Node" => "../javascript/vines_images/node_vine.png",
        "Kotlin" => "../kotlin/vines_images/kt_vine.png",
        "PHP" => "../php/vines_images/php_vine.png",
        "Python" => "../python/vines_images/py_vine.png",
        "React Native" => "../react-native/vines_images/rn_vine.png",
        "Rust" => "../rust/vines_images/rust_vine.png",
        "Swift" => "../swift/vines_images/swift_vine.png"
    ];
    foreach ($parity_configs as $lang => $l_path) {
        if (file_exists($l_path)) {
            $scy_check = new ScyKernel($password, $l_path);
            if ($scy_check->syncPNG($l_path, "load")) {
                $res = $scy_check->getFromPNG($testKey, $password);
                if ($res === $testValue) {
                    echo "✅ PHP to $lang Parity: SUCCESS (Recovered: $res)\n";
                } else {
                    echo "❌ PHP to $lang Parity: FAIL\n";
                }
            }
        }
    }
    exit(0);
} else {
    echo "❌ PHP KV Parity: FAIL\n";
    echo "Expected: " . $testValue . ", Got: [" . $result . "]\n";
    echo "Expected: " . $testValue . ", Got: [" . $result2 . "]\n";
    $scy->deleteDB($path);
    $scy->deleteDB($path2);
    exit(1);
}