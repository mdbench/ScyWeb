<?php
require_once 'ScyKernel.php';

$password = "ScyWeb_Global_Secret_2026";
$imagePath = "../../vines_images/parity_test.ppm";

$testKey = "user";
$testValue = "Amanda";

try {
    // Ensure PPM exists for testing
    if (!file_exists($imagePath)) {
        $dir = dirname($imagePath);
        if (!is_dir($dir)) mkdir($dir, 0777, true);
        
        $fp = fopen($imagePath, 'wb');
        fwrite($fp, "P6\n4000 4000\n255\n");
        // Pre-allocate 48MB file
        $chunk = str_repeat("\0", 1024 * 1024);
        for ($i = 0; $i < (4000 * 4000 * 3) / (1024 * 1024); $i++) {
            fwrite($fp, $chunk);
        }
        fclose($fp);
    }

    $kernel = new ScyKernel($password, $imagePath);

    echo "PHP: Putting key '$testKey'...\n";
    $kernel->put($testKey, $testValue);

    echo "PHP: Getting key '$testKey'...\n";
    $result = $kernel->get($testKey);

    if ($result === $testValue) {
        echo "✅ PHP KV Parity: SUCCESS (Recovered: $result)\n";
        exit(0);
    } else {
        echo "❌ PHP KV Parity: FAIL\n";
        echo "Expected: $testValue, Got: $result\n";
        exit(1);
    }
} catch (Exception $e) {
    echo "❌ PHP Error: " . $e->getMessage() . "\n";
    exit(1);
}