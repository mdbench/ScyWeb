<?php

class ScyKernel {
    private $password;
    private $filePath;
    private $hVal;
    private $canvasSize = 4000;

    public function __construct($pwd, $path) {
        $this->password = $pwd;
        $this->filePath = $path;
        $this->hVal = $this->getHVal($pwd);
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

    private function rot($n, $x, $y, $rx, $ry) {
        if ($ry == 0) {
            if ($rx == 1) {
                $x = $n - 1 - $x;
                $y = $n - 1 - $y;
            }
            return [$y, $x];
        }
        return [$x, $y];
    }

    private function d2xy($n, $d) {
        $x = 0; $y = 0; $t = $d;
        for ($s = 1; $s < $n; $s *= 2) {
            $rx = 1 & (int)($t / 2);
            $ry = 1 & ($t ^ $rx);
            [$x, $y] = $this->rot($s, $x, $y, $rx, $ry);
            $x += $s * $rx;
            $y += $s * $ry;
            $t = (int)($t / 4);
        }
        return [$x, $y];
    }

    public function put($key, $value, $password) {
        $index = $this->deriveIndex($key, $password);
        $curD = $this->hVal + ($index * 1600);
        [$x, $y] = $this->d2xy($this->canvasSize, $curD);

        $fp = fopen($this->filePath, 'r+b');
        $offset = 15 + ($y * $this->canvasSize + $x) * 3;

        for ($i = 0; $i < strlen($value); $i++) {
            fseek($fp, $offset + ($i * 3));
            $pixel = fread($fp, 3);
            if (!$pixel) $pixel = "\0\0\0";
            
            // XOR Obfuscation
            $pixel[0] = $pixel[0] ^ $value[$i];
            
            fseek($fp, $offset + ($i * 3));
            fwrite($fp, $pixel);
        }

        // Null Terminator
        fseek($fp, $offset + (strlen($value) * 3));
        fwrite($fp, "\0\0\0");
        fclose($fp);
    }

    public function get($key, $password) {
        $index = $this->deriveIndex($key, $password);
        $curD = $this->hVal + ($index * 1600);
        [$x, $y] = $this->d2xy($this->canvasSize, $curD);

        $fp = fopen($this->filePath, 'rb');
        $offset = 15 + ($y * $this->canvasSize + $x) * 3;
        $result = "";

        for ($i = 0; ; $i++) {
            fseek($fp, $offset + ($i * 3));
            $pixel = fread($fp, 3);
            if (!$pixel || ord($pixel[0]) === 0) break;
            $result .= $pixel[0];
        }

        fclose($fp);
        return $result;
    }

    public function deleteDB(string $dbPath): bool {
        if (file_exists($dbPath)) {
            return unlink($dbPath);
        }
        return false;
    }
    
}