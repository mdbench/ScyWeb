import fs from 'fs';
import path from 'path';
import ScyKernel from './ScyKernel.js';

async function runSimulation() {
    const testKey = "User";
    const testValue = "Amanda";
    const password = "ScyWeb_Global_Secret_2026";
    const dirName = 'vine_images';
    
    if (!fs.existsSync(dirName)) {
        fs.mkdirSync(dirName, { recursive: true });
    }
    const dbPath = path.join(dirName, 'rn_vine.ppm');

    try {
        // Initialize 15-byte header
        const header = "P6 4000 4000 255\n".substring(0, 15);
        fs.writeFileSync(dbPath, header, 'ascii');

        // Pre-allocate 48MB (Fast Truncate)
        const fd = fs.openSync(dbPath, 'r+');
        fs.truncateSync(dbPath, 48000015);
        fs.closeSync(fd);

        const scy = new ScyKernel(password, dbPath);

        // Execute Operations
        await scy.put(testKey, testValue);
        const result = await scy.get(testKey);

        // Cleanup
        if (fs.existsSync(dbPath)) {
            fs.unlinkSync(dbPath);
        }

        if (result === testValue) {
            console.log(`✅ RN KV Parity: SUCCESS (Recovered: ${result})`);
            process.exit(0);
        } else {
            console.log(`❌ RN KV Parity: FAIL (Expected: ${testValue}, Got: [${result}])`);
            process.exit(1);
        }

    } catch (err) {
        console.error(`❌ Simulation Error: ${err.message}`);
        process.exit(1);
    }
}

runSimulation();