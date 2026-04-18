use std::fs::{File, OpenOptions, self};
use std::io::{Read, Write, Seek, SeekFrom};
use std::path::Path;
use flate2::{read::ZlibDecoder, write::ZlibEncoder, Compression};

pub struct ScyKernel {
    pub password: String,
    pub file_path: String,
    pub canvas_size: i32,
    pub h_val: u32,
    pub db_buffer: Vec<u8>,
}

#[allow(dead_code, unused_parens)]
impl ScyKernel {
    pub fn new(password: String, file_path: String) -> Self {
        let h_val = Self::get_h_val(&password);
        ScyKernel {
            password,
            file_path,
            canvas_size: 4000,
            h_val,
            db_buffer: Vec::new(),
        }
    }

    fn get_h_val(pwd: &str) -> u32 {
        let mut hash: u32 = 7;
        for b in pwd.as_bytes() {
            hash = hash.wrapping_mul(31).wrapping_add(*b as u32);
        }
        let normalized = hash as f64 / 4294967296.0;
        (normalized * 16000000.0).floor() as u32
    }

    fn derive_index(&self, key: &str, password: &str) -> i32 {
        let mut hash: u32 = 0x811c9dc5;
        let prime: u32 = 0x01000193;
        let mut alpha_salt: u32 = 0;
        if !password.is_empty() {
            for b in password.as_bytes() {
                hash ^= *b as u32;
                hash = hash.wrapping_mul(prime);
            }
        }
        for b in key.as_bytes() {
            hash ^= *b as u32;
            hash = hash.wrapping_mul(prime);
            if (*b as char).is_alphabetic() {
                alpha_salt = alpha_salt.wrapping_add((*b as char).to_ascii_lowercase() as u32 - 'a' as u32 + 1);
            }
        }
        let final_val = hash.wrapping_add(alpha_salt);
        let normalized = final_val as f64 / 4294967296.0;
        (normalized * 16000000.0).floor() as i32
    }

    fn d2xy(&self, n: i32, d: i32) -> (i32, i32) {
        let (mut x, mut y) = (0, 0);
        let mut t = d;
        let mut s = 1;
        while s < n {
            let rx = 1 & (t / 2);
            let ry = 1 & (t ^ rx);
            let (nx, ny) = self.rot(s, x, y, rx, ry);
            x = nx + s * rx;
            y = ny + s * ry;
            t /= 4;
            s *= 2;
        }
        (x, y)
    }

    fn rot(&self, n: i32, mut x: i32, mut y: i32, rx: i32, ry: i32) -> (i32, i32) {
        if ry == 0 {
            if rx == 1 {
                x = n - 1 - x;
                y = n - 1 - y;
            }
            return (y, x);
        }
        (x, y)
    }

    fn crypt_byte(&self, c: char, password: &str, position: i32) -> char {
        let mut salt: u32 = 0x811c9dc5;
        for b in password.as_bytes() {
            salt = (salt ^ (*b as u32)).wrapping_mul(16777619);
        }
        let mut mixed = salt ^ (position as u32).wrapping_mul(0xdeadbeef);
        mixed ^= mixed >> 16;
        let key_byte = (mixed & 0xFF) as u8;
        ((c as u8) ^ key_byte) as char
    }

    fn compute_crc(&self, buf: &[u8]) -> u32 {
        let mut crc: u32 = 0xFFFFFFFF;
        for &b in buf {
            crc ^= b as u32;
            for _ in 0..8 {
                let mask = if (crc & 1) == 1 { 0xEDB88320 } else { 0 };
                crc = (crc >> 1) ^ mask;
            }
        }
        !crc
    }

    fn write32<W: Write>(&self, out: &mut W, val: u32) -> std::io::Result<()> {
        let b = val.to_be_bytes();
        out.write_all(&b)
    }

    pub fn put_to_ppm(&self, key: &str, value: &str, password: &str) {
        let index = self.derive_index(key, password);
        let cur_d = self.h_val.wrapping_add((index as u64).wrapping_mul(1600) as u32);
        let (x, y) = self.d2xy(self.canvas_size, cur_d as i32);
        let mut file = match OpenOptions::new().read(true).write(true).open(&self.file_path) {
            Ok(f) => f,
            Err(_) => return,
        };
        let offset = 15 + (y as u64 * self.canvas_size as u64 + x as u64) * 3;
        if file.seek(SeekFrom::Start(offset)).is_err() { return; }
        for (i, c) in value.chars().enumerate() {
            let mut pixel = [0u8; 3];
            if file.read_exact(&mut pixel).is_err() { break; }
            let secure_char = self.crypt_byte(c, password, i as i32);
            pixel[0] = secure_char as u8;
            if file.seek(SeekFrom::Current(-3)).is_err() { break; }
            if file.write_all(&pixel).is_err() { break; }
            if file.seek(SeekFrom::Current(0)).is_err() { break; }
        }
        let _ = file.write_all(&[0u8; 3]);
    }

    pub fn get_from_ppm(&self, key: &str, password: &str) -> String {
        let index = self.derive_index(key, password);
        let cur_d = self.h_val.wrapping_add((index as u64).wrapping_mul(1600) as u32);
        let (x, y) = self.d2xy(self.canvas_size, cur_d as i32);
        let mut file = match File::open(&self.file_path) {
            Ok(f) => f,
            Err(_) => return String::new(),
        };
        let offset = 15 + (y as u64 * self.canvas_size as u64 + x as u64) * 3;
        if file.seek(SeekFrom::Start(offset)).is_err() { return String::new(); }
        let mut result = String::new();
        let mut i = 0;
        loop {
            let mut pixel = [0u8; 3];
            if file.read_exact(&mut pixel).is_err() || pixel[0] == 0 { break; }
            let scrambled = pixel[0] as char;
            result.push(self.crypt_byte(scrambled, password, i));
            i += 1;
        }
        result
    }

    pub fn put_to_png(&mut self, key: &str, value: &str, key_password: &str) {
        if self.db_buffer.is_empty() {
            self.db_buffer = vec![0u8; 48000000];
        }
        let index = self.derive_index(key, key_password);
        let cur_d = self.h_val.wrapping_add((index as u64).wrapping_mul(1600) as u32);
        let (x, y) = self.d2xy(self.canvas_size, cur_d as i32);
        for (i, c) in value.chars().enumerate() {
            let pixel_idx = ((y as usize * self.canvas_size as usize + (x as usize + i)) * 3);
            if pixel_idx + 2 < self.db_buffer.len() {
                let secure_char = self.crypt_byte(c, key_password, i as i32);
                self.db_buffer[pixel_idx] = secure_char as u8;
            }
        }
        let term_idx = ((y as usize * self.canvas_size as usize + (x as usize + value.len())) * 3);
        if term_idx + 2 < self.db_buffer.len() {
            self.db_buffer[term_idx] = 0;
        }
    }

    pub fn get_from_png(&self, key: &str, key_password: &str) -> String {
        if self.db_buffer.is_empty() { return String::new(); }
        let index = self.derive_index(key, key_password);
        let cur_d = self.h_val.wrapping_add((index as u64).wrapping_mul(1600) as u32);
        let (x, y) = self.d2xy(self.canvas_size, cur_d as i32);
        let mut result = String::new();
        let mut i = 0;
        loop {
            let pixel_idx = ((y as usize * self.canvas_size as usize + (x as usize + i)) * 3);
            if pixel_idx + 2 >= self.db_buffer.len() || self.db_buffer[pixel_idx] == 0 {
                break;
            }
            let scrambled = self.db_buffer[pixel_idx] as char;
            result.push(self.crypt_byte(scrambled, key_password, i as i32));
            i += 1;
        }
        result
    }

    pub fn sync_png(&mut self, filename: &str, mode: &str) -> bool {
        let mode_lower = mode.to_lowercase();
        if mode_lower == "load" && !Path::new(filename).exists() {
            self.db_buffer = vec![0u8; 48000000];
            return self.sync_png(filename, "commit");
        }
        if mode_lower == "commit" {
            let mut filtered = Vec::with_capacity(48004000);
            for r in 0..4000 {
                filtered.push(0);
                let start = r * 12000;
                let end = start + 12000;
                filtered.extend_from_slice(&self.db_buffer[start..end]);
            }
            let mut encoder = ZlibEncoder::new(Vec::new(), Compression::default());
            if encoder.write_all(&filtered).is_err() { return false; }
            let compressed: Vec<u8> = match encoder.finish() { Ok(data) => data, Err(_) => return false };
            let mut out = match File::create(filename) { Ok(f) => f, Err(_) => return false };
            let sig: [u8; 8] = [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A];
            let _ = out.write_all(&sig);
            let ihdr: [u8; 17] = [0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x0F, 0xA0, 0x00, 0x00, 0x0F, 0xA0, 0x08, 0x02, 0x00, 0x00, 0x00];
            let _ = self.write32(&mut out, 13);
            let _ = out.write_all(&ihdr);
            let _ = self.write32(&mut out, self.compute_crc(&ihdr));
            let _ = self.write32(&mut out, compressed.len() as u32);
            let _ = out.write_all(b"IDAT");
            let _ = out.write_all(&compressed);
            let mut crc_payload = Vec::with_capacity(4 + compressed.len());
            crc_payload.extend_from_slice(b"IDAT");
            crc_payload.extend_from_slice(&compressed);
            let _ = self.write32(&mut out, self.compute_crc(&crc_payload));
            let _ = self.write32(&mut out, 0);
            let _ = out.write_all(b"IEND");
            let _ = self.write32(&mut out, self.compute_crc(b"IEND"));
            true
        } else if mode_lower == "load" {
            let mut file = match File::open(filename) { Ok(f) => f, Err(_) => return false };
            if file.seek(SeekFrom::Start(33)).is_err() { return false; }
            let mut len_buf = [0u8; 4];
            if file.read_exact(&mut len_buf).is_err() { return false; }
            let c_len = u32::from_be_bytes(len_buf);
            if file.seek(SeekFrom::Current(4)).is_err() { return false; }
            let mut c_data = vec![0u8; c_len as usize];
            if file.read_exact(&mut c_data).is_err() { return false; }
            let mut decoder = ZlibDecoder::new(&c_data[..]);
            let mut decomp = Vec::with_capacity(48004000);
            if decoder.read_to_end(&mut decomp).is_err() { return false; }
            self.db_buffer = vec![0u8; 48000000];
            for r in 0..4000 {
                let src_start = (r * 12001) + 1;
                let src_end = src_start + 12000;
                let dest_start = r * 12000;
                let dest_end = dest_start + 12000;
                self.db_buffer[dest_start..dest_end].copy_from_slice(&decomp[src_start..src_end]);
            }
            true
        } else { false }
    }

    pub fn sync_ppm(&mut self, filename: &str, mode: &str) -> bool {
        let mode_lower = mode.to_lowercase();
        if mode_lower == "load" && !Path::new(filename).exists() {
            self.db_buffer = vec![0u8; 48000000];
            return self.sync_ppm(filename, "commit");
        }
        if mode_lower == "commit" {
            let mut out = match File::create(filename) { Ok(f) => f, Err(_) => return false };
            if write!(out, "P6\n4000 4000\n255\n").is_err() { return false; }
            if out.write_all(&self.db_buffer).is_err() { return false; }
            true
        } else if mode_lower == "load" {
            let mut file = match File::open(filename) { Ok(f) => f, Err(_) => return false };
            if file.seek(SeekFrom::Start(15)).is_err() { return false; }
            self.db_buffer = vec![0u8; 48000000];
            if file.read_exact(&mut self.db_buffer).is_err() { return false; }
            true
        } else { false }
    }

    pub fn create_png_db(&mut self, filename: &str) {
        self.db_buffer = vec![0u8; 48000000];
        let _ = self.sync_png(filename, "commit");
    }

    pub fn create_ppm_db(&self, db_path: &str) {
        match File::create(db_path) {
            Ok(mut ofs) => {
                let header = format!("P6\n{} {}\n255\n", self.canvas_size, self.canvas_size);
                let _ = ofs.write_all(header.as_bytes());
                let zero_row = vec![0u8; (self.canvas_size * 3) as usize];
                for _ in 0..self.canvas_size {
                    let _ = ofs.write_all(&zero_row);
                }
            }
            Err(_) => return,
        }
    }

    pub fn convert_database_format(&mut self, png_path: &str, ppm_path: &str, target_format: &str) -> bool {
        let target = target_format.to_lowercase();
        if target == "ppm" {
            if !self.sync_png(png_path, "load") { return false; }
            let mut ppm = match File::create(ppm_path) { Ok(f) => f, Err(_) => return false };
            let _ = ppm.write_all(b"P6\n4000 4000\n255\n");
            let _ = ppm.write_all(&self.db_buffer);
            true
        } else if target == "png" {
            let mut ppm = match File::open(ppm_path) { Ok(f) => f, Err(_) => return false };
            if ppm.seek(SeekFrom::Start(15)).is_err() { return false; }
            self.db_buffer = vec![0u8; 48000000];
            if ppm.read_exact(&mut self.db_buffer).is_err() { return false; }
            self.sync_png(png_path, "commit")
        } else { false }
    }

    pub fn delete_db(&self, file_path: &str) -> bool {
        fs::remove_file(file_path).is_ok()
    }

    pub fn get_file_size(&self, path: &str) -> u64 {
        std::fs::metadata(path).map(|m| m.len()).unwrap_or(0)
    }

    pub fn validate_db(&self, path: &str) -> bool {
        let raw_data_size: u64 = 48000000;
        let actual = self.get_file_size(path);
        if path.contains(".ppm") {
            actual >= (raw_data_size + 15)
        } else {
            actual >= 1000
        }
    }
}