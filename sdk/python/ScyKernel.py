import os
import mmap
import math
import zlib
import struct
class ScyKernel:
    def __init__(self, password, file_path):
        self.password = password
        self.file_path = file_path
        self.canvas_size = 4000
        self.h_val = self.get_h_val(password)
        self.db_buffer = bytearray()
    def get_h_val(self, pwd):
        hash_val = 7
        for char in pwd:
            hash_val = (hash_val * 31 + ord(char)) & 0xFFFFFFFF
        normalized = hash_val / 4294967296.0
        return int(math.floor(normalized * 16000000.0))
    def derive_index(self, key, password):
        hash_val = 0x811c9dc5
        prime = 0x01000193
        alpha_salt = 0
        if password:
            for char in password:
                hash_val = (hash_val ^ ord(char)) & 0xFFFFFFFF
                hash_val = (hash_val * prime) & 0xFFFFFFFF
        for char in key:
            b = ord(char)
            hash_val = (hash_val ^ b) & 0xFFFFFFFF
            hash_val = (hash_val * prime) & 0xFFFFFFFF
            if char.isalpha():
                alpha_salt += (ord(char.lower()) - ord('a') + 1)
        final_val = (hash_val + alpha_salt) & 0xFFFFFFFF
        normalized = final_val / 4294967296.0
        return int(math.floor(normalized * 16000000.0))
    def d2xy(self, n, d):
        x = y = 0
        t = d
        s = 1
        while s < n:
            rx = 1 & (t // 2)
            ry = 1 & (t ^ rx)
            x, y = self.rot(s, x, y, rx, ry)
            x += s * rx
            y += s * ry
            t //= 4
            s *= 2
        return x, y
    def rot(self, n, x, y, rx, ry):
        if ry == 0:
            if rx == 1:
                x = n - 1 - x
                y = n - 1 - y
            return y, x
        return x, y
    # A bit-perfect, zero-byte overhead encryption layer.
    # XORs the character based on the password's hash and the character's position.
    def crypt_byte(self, c, password, position):
        salt = 0x811c9dc5
        for pc in password:
            salt = ((salt ^ ord(pc)) * 16777619) & 0xFFFFFFFF
        mixed = (salt ^ (position * 0xdeadbeef)) & 0xFFFFFFFF
        mixed ^= (mixed >> 16)
        key_byte = mixed & 0xFF
        return chr(ord(c) ^ key_byte)
    # Crypt byte sanitizer to prevent null collisions
    def sanitize_and_xor(self, raw_char, reverse=False):
        a = 123
        c = 45
        val = ord(raw_char)
        if reverse:
            val_adjusted = val - 1
            inv_a = 179
            return chr(((val_adjusted - c) * inv_a) % 256)
        else:
            transformed = (val * a + c) % 256
            return chr(transformed + 1)
    def sanitize_and_xor(self, raw_char, reverse=False):
        return raw_char
    # Lightweight CRC-32 for PNG Chunk Compliance
    def compute_crc(self, buf):
        crc = 0xFFFFFFFF
        for b in buf:
            crc ^= b
            for _ in range(8):
                mask = -(crc & 1) & 0xFFFFFFFF
                crc = (crc >> 1) ^ (0xEDB88320 & mask)
        return (~crc) & 0xFFFFFFFF
    def write32(self, out, val):
        out.write(struct.pack(">I", val & 0xFFFFFFFF))
    # PPM sow, harvest functions
    def put_to_ppm(self,key,value,password):
        index=self.derive_index(key,password)
        cur_d=self.h_val+(index*1600)
        x,y=self.d2xy(self.canvas_size,cur_d)
        try:
            with open(self.file_path,"r+b") as file:
                offset=15+(y*self.canvas_size+x)*3
                file.seek(offset)
                for i,c in enumerate(value):
                    raw_data = file.read(3)
                    if len(raw_data) < 3:
                        break
                    pixel=bytearray(raw_data)
                    secure_char=self.crypt_byte(c,password,i)
                    sanitized_char = self.sanitize_and_xor(secure_char, reverse=False)
                    pixel[0]=ord(sanitized_char)&0xFF
                    file.seek(-3,1)
                    file.write(pixel)
                    file.seek(file.tell())
                file.write(bytes([0,0,0]))
        except IOError:return
    def get_from_ppm(self, key, password):
        index = self.derive_index(key, password)
        cur_d = self.h_val + (index * 1600)
        x, y = self.d2xy(self.canvas_size, cur_d)
        terminator_count = 0
        try:
            with open(self.file_path, "rb") as file:
                offset = 15 + (y * self.canvas_size + x) * 3
                file.seek(offset)
                result = []
                i = 0
                while True:
                    pixel = file.read(3)
                    if not pixel: break
                    if pixel == b"\x00\x00\x00":
                        terminator_count += 1
                    else:
                        terminator_count = 0
                    restored_char = self.sanitize_and_xor(chr(pixel[0]), reverse=True)
                    result.append(self.crypt_byte(restored_char, password, i))
                    if terminator_count >= 5:
                        #print(f"PPM Termination occurred at pixel {i}.")
                        result = result[:-5]
                        break
                    i += 1
                return "".join(result)
        except IOError:
            return ""
    # PNG sow, harvest functions
    # Writes a value to the RAM buffer.
    # Note: You MUST call sync_png(file, "commit") after calling this to save changes.
    def put_to_png(self, key, value, key_password):
        if not self.db_buffer:
            self.db_buffer = bytearray(48000000)
        index = self.derive_index(key, key_password)
        cur_d = self.h_val + (index * 1600)
        x, y = self.d2xy(self.canvas_size, cur_d)
        for i in range(len(value)):
            pixel_idx = ((y * self.canvas_size) + (x + i)) * 3
            if pixel_idx + 2 < len(self.db_buffer):
                secure_char = self.crypt_byte(value[i], key_password, i)
                sanitized_char = self.sanitize_and_xor(secure_char, reverse=False)
                self.db_buffer[pixel_idx] = ord(sanitized_char) & 0xFF
        term_idx = ((y * self.canvas_size) + (x + len(value))) * 3
        if term_idx + 2 < len(self.db_buffer):
            self.db_buffer[term_idx] = 0
    # Retrieves a value from the RAM buffer.
    # Note: You SHOULD call sync_png(file, "load") before this to ensure fresh data.
    def get_from_png(self, key, key_password):
        if not self.db_buffer:
            return ""
        index = self.derive_index(key, key_password)
        cur_d = self.h_val + (index * 1600)
        x, y = self.d2xy(self.canvas_size, cur_d)
        result = []
        terminator_count = 0
        i = 0
        while True:
            pixel_idx = ((y * self.canvas_size) + (x + i)) * 3
            if pixel_idx + 2 >= len(self.db_buffer):
                break
            r, g, b = self.db_buffer[pixel_idx : pixel_idx + 3]
            if r == 0 and g == 0 and b == 0:
                terminator_count += 1
            else:
                terminator_count = 0
            restored_char = self.sanitize_and_xor(chr(self.db_buffer[pixel_idx]), reverse=True)
            result.append(self.crypt_byte(restored_char, key_password, i))
            if terminator_count >= 5:
                #print(f"PNG Termination occurred at pixel {i}.")
                result = result[:-5]
                break
            i += 1
        return "".join(result)
    # DB sync functions for easier DB handling
    def sync_png(self,filename,mode):
        mode=mode.lower()
        if mode=="load" and not os.path.exists(filename):
            self.db_buffer=bytearray(48000000)
            return self.sync_png(filename,"commit")
        if mode=="commit":
            filtered=bytearray()
            for r in range(4000):
                filtered.append(0)
                start=r*12000
                filtered.extend(self.db_buffer[start:start+12000])
            compressed=zlib.compress(filtered)
            with open(filename,"wb") as out:
                out.write(bytes([0x89,0x50,0x4E,0x47,0x0D,0x0A,0x1A,0x0A]))
                ihdr=bytes([73,72,68,82,0,0,15,160,0,0,15,160,8,2,0,0,0])
                self.write32(out,13)
                out.write(ihdr)
                self.write32(out,self.compute_crc(ihdr))
                self.write32(out,len(compressed))
                out.write(b"IDAT")
                out.write(compressed)
                crc_b=b"IDAT"+compressed
                self.write32(out,self.compute_crc(crc_b))
                self.write32(out,0)
                out.write(b"IEND")
                self.write32(out,self.compute_crc(b"IEND"))
            return True
        elif mode=="load":
            if os.path.getsize(filename)<37:return False
            with open(filename,"rb") as file:
                file.seek(33)
                raw_len=file.read(4)
                if len(raw_len)<4:return False
                c_len=struct.unpack(">I",raw_len)[0]
                file.seek(4,1)
                c_data=file.read(c_len)
            try:
                decomp=zlib.decompress(c_data)
                self.db_buffer=bytearray(48000000)
                for r in range(4000):
                    start=r*12001+1
                    self.db_buffer[r*12000:(r+1)*12000]=decomp[start:start+12000]
                return True
            except:return False
        else:return False
    def sync_ppm(self, filename, mode):
        mode = mode.lower()
        if mode == "load" and not os.path.exists(filename):
            self.db_buffer = bytearray(48000000)
            return self.sync_ppm(filename, "commit")
        if mode == "commit":
            with open(filename, "wb") as out:
                out.write(b"P6\n4000 4000\n255\n")
                out.write(self.db_buffer)
            return True
        elif mode == "load":
            with open(filename, "rb") as file:
                file.seek(15)
                self.db_buffer = bytearray(file.read(48000000))
            return True
        else:return False
    # Blank DB creation functions
    def create_png_db(self, filename):
        self.db_buffer = bytearray(48000000)
        self.sync_png(filename, "commit")
    def create_ppm_db(self, db_path):
        try:
            with open(db_path, "wb") as ofs:
                header = f"P6\n{self.canvas_size} {self.canvas_size}\n255\n".encode()
                ofs.write(header)
                zero_row = bytearray(self.canvas_size * 3)
                for _ in range(self.canvas_size):
                    ofs.write(zero_row)
        except IOError:return
    # DB conversion functions
    def convert_database_format(self, png_path, ppm_path, target_format):
        target_format = target_format.lower()
        if target_format == "ppm":
            if not self.sync_png(png_path, "load"):return False
            with open(ppm_path, "wb") as ppm:
                ppm.write(b"P6\n4000 4000\n255\n")
                ppm.write(bytes(self.db_buffer))
            return True
        elif target_format == "png":
            with open(ppm_path, "rb") as ppm:
                ppm.seek(15)
                self.db_buffer = bytearray(ppm.read(48000000))
            if not self.sync_png(png_path, "commit"):return False
            return True
        else:return False
    # DB Deletion and cleanup functions
    def delete_db(self, db_path: str) -> bool:
        """Removes the database file if it exists."""
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
                return True
            return False
        except OSError:return False
    # DB checking/validating functions
    def get_file_size(self, path):
        try:
            if os.path.exists(path) and os.path.isfile(path):
                return os.path.getsize(path)
        except OSError:return 0
        return 0
    def validate_db(self, path):
        raw_data_size = 48000000
        actual = self.get_file_size(path)
        if ".ppm" in path:
            return actual >= (raw_data_size + 15)
        else:
            return actual >= 1000