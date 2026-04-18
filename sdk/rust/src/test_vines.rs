use scy_rust::ScyKernel;
use std::fs;
use std::path::Path;

fn main() {
    let dir = "vines_images";
    let path_ppm = format!("{}/rust_vine.ppm", dir);
    let path_png = format!("{}/rust_vine.png", dir);
    let test_key = "User";
    let test_value = "Amanda";
    let password = "ScyWeb_Global_Secret_2026";

    if !Path::new(dir).exists() {
        fs::create_dir_all(dir).expect("❌ Failed to create directory");
    }

    let mut scy = ScyKernel::new(password.to_string(), path_ppm.clone());

    scy.create_ppm_db(&path_ppm);
    scy.sync_png(&path_png, "load");

    scy.put_to_ppm(test_key, test_value, password);
    scy.put_to_png(test_key, test_value, password);

    scy.sync_png(&path_png, "commit");
    scy.sync_png(&path_png, "load");

    let result = scy.get_from_ppm(test_key, password);
    let result2 = scy.get_from_png(test_key, password);

    if result == test_value && result2 == test_value {
        let validation_test = if scy.validate_db(&path_ppm) { "Valid" } else { "Invalid" };
        println!("✅ Rust KV Parity: SUCCESS (Recovered: {})", result);
        println!("🧩 PPM is: {}", validation_test);
        
        let size = scy.get_file_size(&path_png);
        println!("📏 Size of Image DB: {} bytes", size);

        let parity_checks = vec![
            ("C++", "../cpp/vines_images/cpp_vine.png"),
            ("Go", "../go/scykernel/vines_images/go_vine.png"),
            ("Java", "../java/vines_images/java_vine.png"),
            ("Node", "../javascript/vines_images/node_vine.png"),
            ("Kotlin", "../kotlin/vines_images/kt_vine.png"),
            ("PHP", "../php/vines_images/php_vine.png"),
            ("Python", "../python/vines_images/py_vine.png"),
            ("React Native", "../react-native/vines_images/rn_vine.png"),
            ("Rust", "../rust/vines_images/rust_vine.png"),
            ("Swift", "../swift/vines_images/swift_vine.png")
        ];

        for (lang, p) in parity_checks {
            if Path::new(p).exists() {
                let mut scy_p = ScyKernel::new(password.to_string(), p.to_string());
                if scy_p.sync_png(p, "load") {
                    let res_p = scy_p.get_from_png(test_key, password);
                    if res_p == test_value {
                        println!("✅ Rust to {} Parity: SUCCESS (Recovered: {})", lang, res_p);
                    } else {
                        println!("❌ Rust to {} Parity: FAIL", lang);
                    }
                }
            }
        }
        std::process::exit(0);
    } else {
        println!("❌ Rust KV Parity: FAIL");
        println!("Expected: {}, Got: PPM [{}], PNG [{}]", test_value, result, result2);
        scy.delete_db(&path_ppm);
        scy.delete_db(&path_png);
        std::process::exit(1);
    }
}