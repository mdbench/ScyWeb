use scy_rust::ScyKernel; // Assumes library is named scy_rust
use std::env;

fn main() {
    let args: Vec<String> = env::args().collect();
    let salt = &args[1];
    let id = &args[2];
    let val = &args[3];
    let path = &args[4];

    let kernel = ScyKernel::new(salt, path);
    kernel.execute(&format!("INSERT INTO m VALUES ('{}','{}')", id, val)).unwrap();
}
