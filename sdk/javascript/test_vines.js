const ScyKernel = require('./ScyKernel');
const fs = require('fs');
const path = require('path');

const password = "ScyWeb_Global_Secret_2026";
const imagePath = path.join(__dirname, "../../vines_images/parity_test.ppm");

const testKey = "user";
const testValue = "Amanda";

function runTest() {
    try {
        // Ensure PPM exists for testing
        if (!fs.existsSync(imagePath)) {
            const dir = path.dirname(imagePath);
            if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
            
            const header = Buffer.from("P6\n4000 4000\n255\n");
            const fd = fs.openSync(imagePath, 'w');
            fs.writeSync(fd, header);
            // Pre-allocate empty file (48MB)
            fs.writeSync(fd, Buffer.alloc(4000 * 4000 * 3), 0, 4000 * 4000 * 3, header.length);
            fs.closeSync(fd);
        }

        const kernel = new ScyKernel(password, imagePath);

        console.log(`Node.js: Putting key '${testKey}'...`);
        kernel.put(testKey, testValue);

        console.log(`Node.js: Getting key '${testKey}'...`);
        const result = kernel.get(testKey);

        if (result === testValue) {
            console.log(`✅ Node.js KV Parity: SUCCESS (Recovered: ${result})`);
            process.exit(0);
        } else {
            console.log(`❌ Node.js KV Parity: FAIL`);
            console.log(`Expected: ${testValue}, Got: ${result}`);
            process.exit(1);
        }
    } catch (err) {
        console.error(`❌ Node.js Error: ${err.message}`);
        process.exit(1);
    }
}

runTest();