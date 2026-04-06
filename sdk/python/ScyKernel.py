import os
import mmap
import math

class ScyKernel:
    def __init__(self, password, file_path):
        self.password = password
        self.file_path = file_path
        self.canvas_size = 4000
        self.h_val = self._get_h_val(password)

    def _get_h_val(self, pwd):
        hash_val = 7
        for char in pwd:
            hash_val = (hash_val * 31 + ord(char)) & 0xFFFFFFFF
        return abs(hash_val % 16000000)

    def _derive_index(self, key):
        # FNV-1a constants
        fnv_offset_basis = 0x811c9dc5
        fnv_prime = 0x01000193
        hash_val = fnv_offset_basis
        alpha_salt = 0
        
        lower_key = key.lower()
        for i, char in enumerate(key):
            # FNV-1a Math (32-bit unsigned)
            hash_val ^= ord(char)
            hash_val = (hash_val * fnv_prime) & 0xFFFFFFFF
            
            # Alphabet Salt (a=1, b=2...)
            if lower_key[i].isalpha():
                alpha_salt += (ord(lower_key[i]) - ord('a') + 1)
        
        return abs(hash_val + alpha_salt) % 16000000

    def _rot(self, n, x, y, rx, ry):
        if ry == 0:
            if rx == 1:
                x = n - 1 - x
                y = n - 1 - y
            return y, x
        return x, y

    def _d2xy(self, n, d):
        x, y = 0, 0
        t = d
        s = 1
        while s < n:
            rx = 1 & (t // 2)
            ry = 1 & (t ^ rx)
            x, y = self._rot(s, x, y, rx, ry)
            x += s * rx
            y += s * ry
            t //= 4
            s *= 2
        return x, y

    def put(self, key, value):
        index = self._derive_index(key)
        cur_d = self.h_val + (index * 1000)
        x, y = self._d2xy(self.canvas_size, cur_d)
        
        data = value.encode('utf-8')
        offset = 15 + (y * self.canvas_size + x) * 3
        
        with open(self.file_path, "r+b") as f:
            # Memory map the file for random access
            mm = mmap.mmap(f.fileno(), 0)
            
            for i, byte in enumerate(data):
                pixel_pos = offset + (i * 3)
                # XOR Obfuscation on the Red channel
                original_r = mm[pixel_pos]
                mm[pixel_pos] = original_r ^ byte
            
            # Write Null Terminator
            term_pos = offset + (len(data) * 3)
            mm[term_pos:term_pos+3] = b'\x00\x00\x00'
            mm.close()

    def get(self, key):
        index = self._derive_index(key)
        cur_d = self.h_val + (index * 1000)
        x, y = self._d2xy(self.canvas_size, cur_d)
        
        offset = 15 + (y * self.canvas_size + x) * 3
        result = bytearray()
        
        with open(self.file_path, "rb") as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            
            i = 0
            while True:
                pixel_pos = offset + (i * 3)
                if pixel_pos >= mm.size() or mm[pixel_pos] == 0:
                    break
                result.append(mm[pixel_pos])
                i += 1
            
            mm.close()
        return result.decode('utf-8')