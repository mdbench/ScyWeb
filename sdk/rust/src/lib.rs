use std::fs::OpenOptions;
use std::io::{Read, Write, Seek, SeekFrom};

pub struct ScyKernel {
    password: String,
    file_path: String,
    h_val: i32,
    canvas_size: i32,
}

impl ScyKernel {
    pub fn new(password: &str, file_path: &str) -> Self {
        let mut kernel = ScyKernel {
            password: password.to_string(),
            file_path: file_path.to_string(),
            h_val: 0,
            canvas_size: 4000,
        };
        kernel.h_val = kernel.get_h_val(password);
        kernel
    }

    fn get_h_val(&self, pwd: &str) -> i32 {
        let mut hash: i32 = 7;
        for c in pwd.chars() {
            hash = hash.wrapping_mul(31).wrapping_add(c as i32);
        }
        (((hash as u32) as f64 / 4294967296.0) * 16000000.0) as i32
    }

    // Deterministic FNV-1a + Alphabet Salt for Cross-Language Parity
    fn derive_index(&self, key: &str) -> i32 {
        let mut hash: u32 = 0x811c9dc5;
        let prime: u32 = 0x01000193;
        let mut alpha_salt: i64 = 0;

        let lower_key = key.to_lowercase();
        for (i, c) in key.chars().enumerate() {
            // FNV-1a Math (32-bit unsigned wrapping)
            hash ^= c as u32;
            hash = hash.wrapping_mul(prime);

            // Alphabet Salt (a=1, b=2...)
            if c.is_alphabetic() {
                let salt_val = (lower_key.chars().nth(i).unwrap() as i64) - ('a' as i64) + 1;
                alpha_salt += salt_val;
            }
        }
        
        let combined = (hash as i64 + alpha_salt) as u32;
        ((combined as f64 / 4294967296.0) * 16000000.0) as i32
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

    pub fn put(&self, key: &str, value: &str) -> std::io::Result<()> {
        let index = self.derive_index(key);
        let cur_d = self.h_val + (index * 1600);
        let (x, y) = self.d2xy(self.canvas_size, cur_d);

        let mut file = OpenOptions::new().read(true).write(true).open(&self.file_path)?;
        let offset = 15 + (y as u64 * self.canvas_size as u64 + x as u64) * 3;
        let bytes = value.as_bytes();

        for (i, &byte) in bytes.iter().enumerate() {
            let pos = offset + (i as u64 * 3);
            file.seek(SeekFrom::Start(pos))?;
            let mut pixel = [0u8; 3];
            file.read_exact(&mut pixel)?;
            
            // XOR Obfuscation
            pixel[0] ^= byte;
            
            file.seek(SeekFrom::Start(pos))?;
            file.write_all(&pixel)?;
        }

        // Write Null Terminator
        file.seek(SeekFrom::Start(offset + (bytes.len() as u64 * 3)))?;
        file.write_all(&[0, 0, 0])?;
        Ok(())
    }

    pub fn get(&self, key: &str) -> std::io::Result<String> {
        let index = self.derive_index(key);
        let cur_d = self.h_val + (index * 1600);
        let (x, y) = self.d2xy(self.canvas_size, cur_d);

        let mut file = OpenOptions::new().read(true).open(&self.file_path)?;
        let offset = 15 + (y as u64 * self.canvas_size as u64 + x as u64) * 3;
        let mut result = Vec::new();

        let mut i = 0;
        loop {
            let pos = offset + (i * 3);
            file.seek(SeekFrom::Start(pos))?;
            let mut pixel = [0u8; 3];
            if file.read_exact(&mut pixel).is_err() || pixel[0] == 0 {
                break;
            }
            result.push(pixel[0]);
            i += 1;
        }

        Ok(String::from_utf8_lossy(&result).into_owned())
    }
}