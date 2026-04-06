use std::io::{Write, Seek, SeekFrom};
use std::fs::OpenOptions;
fn main() {
    let p = "parity_images/rust_database.ppm";
    let mut f = std::fs::File::create(p).unwrap();
    f.write_all(b"P6\n4000 4000\n255\n").unwrap();
    f.set_len(48000017).unwrap();
    let mut f = OpenOptions::new().write(true).open(p).unwrap();
    for i in 1..=4000 {
        let mut hasher = sha2::Sha256::new();
        hasher.update(format!("{}{}{}", "Node_Alpha_", i, "ScyWeb_Global_Parity_2026").as_bytes());
        let h = format!("{:x}", hasher.finalize());
        let x = u64::from_str_radix(&h[0..4], 16).unwrap() % 4000;
        let y = u64::from_str_radix(&h[4..8], 16).unwrap() % 4000;
        let o = 17 + (y * 4000 + x) * 3;
        f.seek(SeekFrom::Start(o)).unwrap();
        f.write_all(format!("UPDATE user SET status='ACTIVE' WHERE id={}\0", i).as_bytes()).unwrap();
    }
}
