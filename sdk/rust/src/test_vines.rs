use scy_rust::ScyKernel; 
use std::fs::{self, File, OpenOptions};
use std::io::Write;
use std::path::Path;

fn main() {
    let test_key = "User";
    let test_value = "Amanda";
    let password = "ScyWeb_Global_Secret_2026";
    let db_dir = "vines_images";
    let db_path = format!("{}/rust_vine.ppm", db_dir);

    // 1. PHYSICAL FILE SETUP
    if !Path::new(db_dir).exists() {
        fs::create_dir_all(db_dir).expect("❌ Failed to create directory");
    }

    let file = File::create(&db_path).expect("❌ Failed to create database file");
    
    // Exact 15-byte header parity: "P6 4000 4000 255\n"
    let header = b"P6 4000 4000 255\n";
    file.set_len(48_000_015).expect("❌ Failed to allocate 48MB");
    
    let mut file_handle = OpenOptions::new().write(true).open(&db_path).unwrap();
    file_handle.write_all(&header[..15]).expect("❌ Failed to write header");

    // 2. INITIALIZE KERNEL
    let scy = ScyKernel::new(password, &db_path);

    // 3. SOW: Put operation
    scy.put(test_key, test_value, password).expect("❌ Rust SDK Put Error");

    // 4. HARVEST: Get operation
    let result = scy.get(test_key, password).expect("❌ Rust SDK Get Error");

    if result == test_value {
        println!("✅ Rust KV Parity: SUCCESS (Recovered: {})", result);
        let _ = scy.delete_db(&db_path);
        std::process::exit(0);
    } else {
        println!("❌ Rust KV Parity: FAIL. Expected {}, Got [{}]", test_value, result);
        let _ = scy.delete_db(&db_path);
        std::process::exit(1);
    }
}