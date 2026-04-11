const fs = require('fs');
const path = require('path');
const ScyKernel = require('./ScyKernel'); // Importing your JS class

async function runTest() {
    const testKey = "User";
    const testValue = "Amanda";
    const password = "ScyWeb_Global_Secret_2026";
    const dbDir = path.join(__dirname, 'vines_images');
    const dbPath = path.join(dbDir, 'js_vine.ppm');

    // PHYSICAL FILE SETUP
    if (!fs.existsSync(dbDir)) {
        fs.mkdirSync(dbDir, { recursive: true });
    }

    // Create the 48MB database with the 15-byte header
    const header = Buffer.from("P6 4000 4000 255\n");
    const fd = fs.openSync(dbPath, 'w');
    
    // Write exact 15 bytes for header parity
    fs.writeSync(fd, header, 0, 15);
    
    // Fast-allocate the rest of the 48MB (4000 * 4000 * 3)
    // Total size: 48,000,015 bytes
    fs.ftruncateSync(fd, 48000015);
    fs.closeSync(fd);

    // INITIALIZE KERNEL
    const scy = new ScyKernel(password, dbPath);

    // SOW: Put the data (Uses 1600 offset internally)
    try {
        await scy.put(testKey, testValue, password);
    } catch (err) {
        console.error(`❌ JS SDK Put Error: ${err.message}`);
        process.exit(1);
    }

    // HARVEST: Get the data
    try {
        const result = await scy.get(testKey, password);
        if (result === testValue) {
            console.log(`✅ JS KV Parity: SUCCESS (Recovered: ${result})`);
            scy.deleteDB(dbPath);
            process.exit(0);
        } else {
            console.log(`❌ JS KV Parity: FAIL`);
            console.log(`Expected: ${testValue}, Got: [${result}]`);
            scy.deleteDB(dbPath);
            process.exit(1);
        }
    } catch (err) {
        console.error(`❌ JS SDK Get Error: ${err.message}`);
        process.exit(1);
    }
}

runTest();