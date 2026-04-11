<?php
require_once 'ScyKernel.php';

function runTest() {
    $testKey = "User";
    $testValue = "Amanda";
    $password = "ScyWeb_Global_Secret_2026";
    $dbDir = "vines_images";
    $dbPath = $dbDir . "/php_vine.ppm";

    // PHYSICAL FILE SETUP
    if (!is_dir($dbDir)) {
        mkdir($dbDir, 0755, true);
    }

    $f = fopen($dbPath, "wb+");
    if (!$f) {
        echo "❌ Failed to create database file.\n";
        exit(1);
    }

    // Write exact 15-byte header parity: "P6 4000 4000 25"
    $header = "P6 4000 4000 255\n";
    fwrite($f, substr($header, 0, 15));

    // Allocate 48MB (4000 * 4000 * 3) using ftruncate
    ftruncate($f, 48000015);
    fclose($f);

    // INITIALIZE KERNEL
    $scy = new ScyKernel($password, $dbPath);

    // SOW: Put operation (Must use 1600 offset internally)
    try {
        $scy->put($testKey, $testValue, $password);
    } catch (Exception $e) {
        echo "❌ PHP SDK Put Error: " . $e->getMessage() . "\n";
        exit(1);
    }

    // HARVEST: Get operation
    try {
        $result = $scy->get($testKey, $password);

        if ($result === $testValue) {
            echo "✅ PHP KV Parity: SUCCESS (Recovered: $result)\n";
            $scy->deleteDB($dbPath);
            exit(0);
        } else {
            echo "❌ PHP KV Parity: FAIL\n";
            echo "Expected: $testValue, Got: [$result]\n";
            $scy->deleteDB($dbPath);
            exit(1);
        }
    } catch (Exception $e) {
        echo "❌ PHP SDK Get Error: " . $e->getMessage() . "\n";
        exit(1);
    }
}

runTest();