const fs = require('fs');
const pathActual = require('path');
// Replace './ScyKernel' with the actual path to your class file
const ScyKernel = require('./ScyKernel'); 

async function runTest() {
    const dir = "vines_images";
    const path = pathActual.join(dir, "node_vine.ppm");
    const path2 = pathActual.join(dir, "node_vine.png");
    const testKey = "User";
    const testValue = "Amanda";
    const password = "ScyWeb_Global_Secret_2026";

    // Ensure the local folder exists
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir);
    }
    
    // Instantiating 'scy' with the password and the local path
    const scy = new ScyKernel(password, path);

    // Creating the test DBs
    scy._createPPM_DB(path);
    scy._syncPNG(path2, "load");

    // Test both PPM and PNG DBs
    scy._putToPPM(testKey, testValue, password);
    scy._putToPNG(testKey, testValue, password);

    // sync changes and refresh
    scy._syncPNG(path2, "commit");
    scy._syncPNG(path2, "load");

    // Retrieve the results from both DBs
    const result = scy._getFromPPM(testKey, password);
    const result2 = scy._getFromPNG(testKey, password);

    // Output Comparison
    if (result === testValue && result2 === testValue) {
        const isValid = scy._validateDB(path) ? "Valid" : "Invalid";
        console.log(`✅ Node.js KV Parity: SUCCESS (Recovered: ${result})`);
        console.log(`🧩 PPM is: ${isValid}`);
        const size = scy._getFileSize(path2);
        console.log(`📏 Size of Image DB: ${size} bytes`);
        // fs.unlinkSync(path);
        // fs.unlinkSync(path2);
        const parityConfigs = [
            ["C++", "../cpp/vines_images/cpp_vine.png"],
            ["Go", "../go/scykernel/vines_images/go_vine.png"],
            ["Java", "../java/vines_images/java_vine.png"],
            ["Node", "../javascript/vines_images/node_vine.png"],
            ["Kotlin", "../kotlin/vines_images/kt_vine.png"],
            ["PHP", "../php/vines_images/php_vine.png"],
            ["Python", "../python/vines_images/py_vine.png"],
            ["React Native", "../reace-native/vines_images/rn_vine.png"],
            ["Rust", "../rust/vines_images/rust_vine.png"],
            ["Swift", "../swift/vines_images/swift_vine.png"]
        ];
        for (const [lang, lPath] of parityConfigs) {
            if (fs.existsSync(lPath)) {
                const scyCheck = new ScyKernel(password, lPath);
                if (scyCheck._syncPNG(lPath, "load")) {
                    const res = scyCheck._getFromPNG(testKey, password);
                    if (res === testValue) {
                        console.log(`✅ JS to ${lang} Parity: SUCCESS (Recovered: ${res})`);
                    } else {
                        console.log(`❌ JS to ${lang} Parity: FAIL`);
                    }
                }
            }
        }
        process.exit(0);
    } else {
        console.error("❌ Node.js KV Parity: FAIL");
        console.error(`Expected: ${testValue}, Got PPM: [${result}]`);
        console.error(`Expected: ${testValue}, Got PNG: [${result2}]`);
        fs.unlinkSync(path);
        fs.unlinkSync(path2);
        process.exit(1);
    }
}

runTest();