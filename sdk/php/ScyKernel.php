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
    private function deriveIndex($key) {
        $hash = 0x811c9dc5;
        $prime = 0x01000193;
        $alphaSalt = 0;

        $lowerKey = strtolower($key);
        for ($i = 0; $i < strlen($key); $i++) {
            // FNV-1a Math: XOR then Multiply (constrained to 32-bit)
            $hash ^= ord($key[$i]);
            // Multiply and immediately mask to 32-bits
            $hash = ($hash * $prime) & 0xFFFFFFFF;

            // Alphabet Salt (a=1, b=2...)
            if (ctype_alpha($key[$i])) {
                $alphaSalt += (ord($lowerKey[$i]) - ord('a') + 1);
            }
        }
        
        // Combine, cast to unsigned float, and project
        $finalVal = (float)sprintf('%u', ($hash + $alphaSalt) & 0xFFFFFFFF);
        return (int)floor(($finalVal / 4294967296.0) * 16000000);
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

    public function put($key, $value) {
        $index = $this->deriveIndex($key);
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

    public function get($key) {
        $index = $this->deriveIndex($key);
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
}