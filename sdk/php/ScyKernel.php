<?php

class ScyKernel {
    private $password;
    private $filePath;
    private $hVal;
    private $canvasSize = 4000;
    private $dbBuffer;

    public function __construct($pwd, $path) {
        $this->password = $pwd;
        $this->filePath = $path;
        $this->hVal = $this->getHVal($pwd);
        $this->dbBuffer = str_repeat("\0", 48000000);
    }

    private function getHVal($pwd) {
        $hash = 7;
        for ($i = 0; $i < strlen($pwd); $i++) {
            // Force 32-bit wrapping math
            $hash = ($hash * 31 + ord($pwd[$i])) & 0xFFFFFFFF;
        }
        // Vectorial Normalization: (Unsigned 32-bit / 2^32) * 16M
        $unsignedHash = (float)sprintf('%u', $hash);
        return (int)floor(($unsignedHash / 4294967296.0) * 16000000);
    }

    // Deterministic FNV-1a + Alphabet Salt for Cross-Language Parity
    private function deriveIndex(string $key, string $password): int {
        $hash = 0x811c9dc5;
        $prime = 0x01000193;
        $alphaSalt = 0;
        $passBytes = unpack('C*', $password);
        foreach ($passBytes as $b) {
            $hash ^= $b;
            $hash = ($hash * $prime) & 0xFFFFFFFF;
        }
        $keyBytes = unpack('C*', $key);
        foreach ($keyBytes as $b) {
            $hash ^= $b;
            $hash = ($hash * $prime) & 0xFFFFFFFF;
            $char = chr($b);
            if (ctype_alpha($char)) {
                $alphaSalt += (ord(strtolower($char)) - ord('a') + 1);
            }
        }
        $finalVal = ($hash + $alphaSalt) & 0xFFFFFFFF;
        $normalized = ($finalVal / 4294967296.0) * 16000000.0;
        return (int)floor($normalized);
    }

    private function d2xy($n, $d, &$x, &$y) {
        $x = $y = 0;
        $t = $d;
        for ($s = 1; $s < $n; $s *= 2) {
            $rx = 1 & (int)($t / 2);
            $ry = 1 & ($t ^ $rx);
            $this->rot($s, $x, $y, $rx, $ry);
            $x += $s * $rx;
            $y += $s * $ry;
            $t = (int)($t / 4);
        }
    }

    private function rot($n, &$x, &$y, $rx, $ry) {
        if ($ry == 0) {
            if ($rx == 1) {
                $x = $n - 1 - $x;
                $y = $n - 1 - $y;
            }
            $temp = $x;
            $x = $y;
            $y = $temp;
        }
    }

    /**
    * A bit-perfect, zero-byte overhead encryption layer.
    * XORs the character based on the password's hash and the character's position.
    */
    private function cryptByte($c, $password, $position) {
        $salt = 0x811c9dc5;
        $len = strlen($password);
        for ($i = 0; $i < $len; $i++) {
            $salt = (($salt ^ ord($password[$i])) * 16777619) & 0xFFFFFFFF;
        }
        $mixed = ($salt ^ (($position * 0xdeadbeef) & 0xFFFFFFFF)) & 0xFFFFFFFF;
        $mixed ^= ($mixed >> 16);
        $keyByte = $mixed & 0xFF;
        return chr(ord($c) ^ $keyByte);
    }

    // Lightweight CRC-32 for PNG Chunk Compliance
    private function compute_crc($buf, $len) {
        $crc = 0xFFFFFFFF;
        for ($i = 0; $i < $len; $i++) {
            $crc ^= ord($buf[$i]);
            for ($j = 0; $j < 8; $j++) {
                $mask = ($crc & 1) ? 0xEDB88320 : 0;
                $crc = (($crc >> 1) & 0x7FFFFFFF) ^ $mask;
            }
        }
        return ~$crc & 0xFFFFFFFF;
    }

    private function write32($out, $val) {
        $b = pack("N", $val);
        fwrite($out, $b);
    }

    // PPM sow, harvest functions
    public function putToPPM($key, $value, $password) {
        $x = 0; $y = 0;
        $index = $this->deriveIndex($key, $password);
        $curD = $this->hVal + ($index * 1600);
        $this->d2xy($this->canvasSize, $curD, $x, $y);
        $file = fopen($this->filePath, "r+b");
        if (!$file) return;
        $offset = 15 + ($y * $this->canvasSize + $x) * 3;
        fseek($file, $offset);
        $i = 0;
        for ($j = 0; $j < strlen($value); $j++) {
            $pixel = fread($file, 3);
            if (strlen($pixel) < 3) break;
            $secureChar = $this->cryptByte($value[$j], $password, $i);
            $pixel[0] = $secureChar;
            fseek($file, -3, SEEK_CUR);
            fwrite($file, $pixel);
            fseek($file, 0, SEEK_CUR);
            $i++;
        }
        fwrite($file, "\0\0\0");
        fclose($file);
    }

    public function getFromPPM($key, $password) {
        $x = 0; $y = 0;
        $index = $this->deriveIndex($key, $password);
        $curD = $this->hVal + ($index * 1600);
        $this->d2xy($this->canvasSize, $curD, $x, $y);
        $file = fopen($this->filePath, "rb");
        if (!$file) return "";
        $offset = 15 + ($y * $this->canvasSize + $x) * 3;
        fseek($file, $offset);
        $result = "";
        $i = 0;
        while (!feof($file)) {
            $pixel = fread($file, 3);
            if (strlen($pixel) < 3 || ord($pixel[0]) === 0) break;
            $scrambled = $pixel[0];
            $result .= $this->cryptByte($scrambled, $password, $i);
            $i++;
        }
        fclose($file);
        return $result;
    }

    // PNG sow, harvest functions
    /**
    * Writes a value to the RAM buffer.
    * Note: You MUST call syncPNG(file, "commit") after calling this to save changes.
    */
    public function putToPNG($key, $value, $keyPassword) {
        if (empty($this->dbBuffer)) {
            $this->dbBuffer = str_repeat("\0", 48000000);
        }
        $x = 0; $y = 0;
        $index = $this->deriveIndex($key, $keyPassword);
        $curD = $this->hVal + ($index * 1600);
        $this->d2xy($this->canvasSize, $curD, $x, $y);
        for ($i = 0; $i < strlen($value); $i++) {
            $pixelIdx = (($y * $this->canvasSize) + ($x + $i)) * 3;
            if ($pixelIdx + 2 < strlen($this->dbBuffer)) {
                $secureChar = $this->cryptByte($value[$i], $keyPassword, $i);
                $this->dbBuffer[$pixelIdx] = $secureChar;
            }
        }
        $termIdx = (($y * $this->canvasSize) + ($x + strlen($value))) * 3;
        if ($termIdx + 2 < strlen($this->dbBuffer)) {
            $this->dbBuffer[$termIdx] = "\0";
        }
    }

    /**
    * Retrieves a value from the RAM buffer.
    * Note: You SHOULD call syncPNG(file, "load") before this to ensure fresh data.
    */
    public function getFromPNG($key, $keyPassword) {
        if (empty($this->dbBuffer)) return "";
        $x = 0; $y = 0;
        $index = $this->deriveIndex($key, $keyPassword);
        $curD = $this->hVal + ($index * 1600);
        $this->d2xy($this->canvasSize, $curD, $x, $y);
        $result = "";
        $i = 0;
        while (true) {
            $pixelIdx = (($y * $this->canvasSize) + ($x + $i)) * 3;
            if ($pixelIdx + 2 >= strlen($this->dbBuffer) || ord($this->dbBuffer[$pixelIdx]) === 0) {
                break;
            }
            $result .= $this->cryptByte($this->dbBuffer[$pixelIdx], $keyPassword, $i);
            $i++;
        }
        return $result;
    }

    // DB sync functions for easier DB handling
    function syncPNG($filename, $mode) {
        $mode = strtolower($mode);
        if ($mode == "load" && !file_exists($filename)) {
            $this->dbBuffer = str_repeat("\0", 48000000);
            return $this->syncPNG($filename, "commit");
        }
        if ($mode == "commit") {
            $filtered = "";
            for ($r = 0; $r < 4000; $r++) {
                $filtered .= "\0";
                $filtered .= substr($this->dbBuffer, $r * 12000, 12000);
            }
            $compressed = gzcompress($filtered, 9);
            if ($compressed === false) return false;
            $out = fopen($filename, "wb");
            if (!$out) return false;
            fwrite($out, "\x89PNG\r\n\x1a\n");
            $ihdrType = "IHDR";
            $ihdrPayload = pack("NNCCCCC", 4000, 4000, 8, 2, 0, 0, 0);
            $this->write32($out, 13);
            fwrite($out, $ihdrType);
            fwrite($out, $ihdrPayload);
            $this->write32($out, $this->compute_crc($ihdrType . $ihdrPayload, 17));
            $idatType = "IDAT";
            $this->write32($out, strlen($compressed));
            fwrite($out, $idatType);
            fwrite($out, $compressed);
            $this->write32($out, $this->compute_crc($idatType . $compressed, strlen($compressed) + 4));
            $iendType = "IEND";
            $this->write32($out, 0);
            fwrite($out, $iendType);
            $this->write32($out, $this->compute_crc($iendType, 4));
            fclose($out);
            return true;
        } else if ($mode == "load") {
            $handle = fopen($filename, "rb");
            if (!$handle) return false;
            fseek($handle, 8);
            $idatData = "";
            while (!feof($handle)) {
                $chunkLenData = fread($handle, 4);
                if (strlen($chunkLenData) < 4) break;
                $chunkLen = unpack("N", $chunkLenData)[1];
                $chunkType = fread($handle, 4);
                if ($chunkType === "IDAT") {
                    $idatData .= fread($handle, $chunkLen);
                    fread($handle, 4);
                } else if ($chunkType === "IEND") {
                    break;
                } else {
                    fseek($handle, $chunkLen + 4, SEEK_CUR);
                }
            }
            fclose($handle);
            if (empty($idatData)) return false;
            $decompressed = @gzuncompress($idatData);
            if ($decompressed === false) return false;
            $this->dbBuffer = "";
            for ($r = 0; $r < 4000; $r++) {
                $this->dbBuffer .= substr($decompressed, ($r * 12001) + 1, 12000);
            }
            //echo "✅ PNG Load Successful:".$filename."\n";
            return true;
        }
        return false;
    }

    public function syncPPM($filename, $mode) {
        $mode = strtolower($mode);
        if ($mode == "load" && !file_exists($filename)) {
            echo "⚠️ PPM Database not found. Initializing new raw store...\n";
            $this->dbBuffer = str_repeat("\0", 48000000);
            return $this->syncPPM($filename, "commit");
        }
        if ($mode == "commit") { // COMMIT MODE (RAM -> Disk)
            $out = fopen($filename, "wb");
            if (!$out) return false;
            fwrite($out, "P6\n4000 4000\n255\n");
            fwrite($out, $this->dbBuffer);
            fclose($out);
            echo "✅ PPM Commit Successful: $filename\n";
            return true;
        } else if ($mode == "load") { // LOAD MODE (Disk -> RAM)
            $file = fopen($filename, "rb");
            if (!$file) return false;
            fseek($file, 15);
            $this->dbBuffer = fread($file, 48000000);
            fclose($file);
            echo "✅ PPM Load Successful: $filename\n";
            return true;
        } else {
            echo "❌ Invalid Sync Mode. Use 'Commit' or 'Load'.\n";
            return false;
        }
    }

    // Blank DB creation functions
    public function createPNG_DB($filename) {
        $this->dbBuffer = str_repeat("\0", 48000000);
        if ($this->syncPNG($filename, "commit")) {
            echo "✅ PNG initialized and loaded into buffer: $filename\n";
        } else {
            echo "❌ Failed to initialize PNG database file.\n";
        }
    }

    public function createPPM_DB($dbPath) {
        $ofs = fopen($dbPath, "wb");
        if (!$ofs) {
            echo "❌ Error: Could not create PPM database\n";
            return;
        }
        fwrite($ofs, "P6\n" . $this->canvasSize . " " . $this->canvasSize . "\n255\n");
        $zeroRow = str_repeat("\0", $this->canvasSize * 3);
        for ($i = 0; $i < $this->canvasSize; $i++) {
            fwrite($ofs, $zeroRow);
        }
        fclose($ofs);
        echo "✅ PPM Database Ready (Isolated from RAM): $dbPath\n";
    }

    // DB conversion functions
    public function convertDatabaseFormat($pngPath, $ppmPath, $targetFormat) {
        $targetFormat = strtolower($targetFormat);
        if ($targetFormat == "ppm") {
            if (!$this->syncPNG($pngPath, "load")) {
                echo "❌ Failed to load PNG database.\n";
                return false;
            }
            $ppm = fopen($ppmPath, "wb");
            if (!$ppm) return false;
            fwrite($ppm, "P6\n4000 4000\n255\n");
            fwrite($ppm, $this->dbBuffer);
            fclose($ppm);
            echo "✅ Converted PNG to PPM (48MB Raw Volume)\n";
            return true;
        } elseif ($targetFormat == "png") {
            $ppm = fopen($ppmPath, "rb");
            if (!$ppm) return false;
            fseek($ppm, 15);
            $this->dbBuffer = fread($ppm, 48000000);
            fclose($ppm);
            if (!$this->syncPNG($pngPath, "commit")) {
                echo "❌ Failed to compress and save PNG database.\n";
                return false;
            }
            echo "✅ Converted PPM to PNG\n";
            return true;
        } else {
            echo "❌ Invalid target format. Use 'PNG' or 'PPM'.\n";
            return false;
        }
    }

    // DB Deletion and cleanup functions
    public function deleteDB(string $dbPath): bool {
        if (file_exists($dbPath)) {
            return unlink($dbPath);
        }
        return false;
    }

    // DB checking/validating functions
    public function getFileSize($path) {
        if (file_exists($path) && is_file($path)) {
            return filesize($path);
        }
        return 0;
    }

    public function validateDB($path) {
        $rawDataSize = 48000000;
        $actual = $this->getFileSize($path);
        if (strpos($path, ".ppm") !== false) {
            return $actual >= ($rawDataSize + 15);
        } else {
            return $actual >= $rawDataSize;
        }
    }
    
}