use scy_rust::ScyKernel;
use std::fs;
use std::process;

fn main() {
    let password = "ScyWeb_Global_Secret_2026";
    let image_path = "../../vines_images/parity_test.ppm";
    
    let test_key = "user";
    let test_value = "Amanda";

    // Ensure directory and dummy PPM exist for CI
    if !fs::metadata("../../vines_images").is_ok() {
        fs::create_dir_all("../../vines_images").unwrap();
    }

    if !fs::metadata(image_path).is_ok() {
        let mut header = Vec::from("P6\n4000 4000\n255\n");
        let empty_payload = vec![0u8; 4000 * 4000 * 3];
        header.extend(empty_payload);
        fs::write(image_path, header).expect("Unable to create test image");
    }

    let kernel = ScyKernel::new(password, image_path);

    println!("Rust: Putting key '{}'...", test_key);
    if let Err(e) = kernel.put(test_key, test_value) {
        eprintln!("❌ Rust Error during Put: {}", e);
        process::exit(1);
    }

    println!("Rust: Getting key '{}'...", test_key);
    match kernel.get(test_key) {
        Ok(result) => {
            if result == test_value {
                println!("✅ Rust KV Parity: SUCCESS (Recovered: {})", result);
                process::exit(0);
            } else {
                println!("❌ Rust KV Parity: FAIL. Expected: {}, Got: {}", test_value, result);
                process::exit(1);
            }
        }
        Err(e) => {
            eprintln!("❌ Rust Error during Get: {}", e);
            process::exit(1);
        }
    }
}