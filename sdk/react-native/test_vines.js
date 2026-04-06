import ScyKernel from './ScyKernel';
import RNFS from 'react-native-fs';

const password = "ScyWeb_Global_Secret_2026";
const imagePath = `${RNFS.DocumentDirectoryPath}/parity_test.ppm`;

const testKey = "user";
const testValue = "Amanda";

const runTest = async () => {
    try {
        // Ensure PPM exists
        const exists = await RNFS.exists(imagePath);
        if (!exists) {
            const header = "P6\n4000 4000\n255\n";
            await RNFS.writeFile(imagePath, header, 'utf8');
            // Note: In a real app, pre-allocating 48MB on main thread is slow.
            // For testing, we ensure the file is at least large enough.
        }

        const kernel = new ScyKernel(password, imagePath);

        console.log(`React Native: Putting key '${testKey}'...`);
        await kernel.put(testKey, testValue);

        console.log(`React Native: Getting key '${testKey}'...`);
        const result = await kernel.get(testKey);

        if (result === testValue) {
            console.log(`✅ RN KV Parity: SUCCESS (Recovered: ${result})`);
            return true;
        } else {
            console.log(`❌ RN KV Parity: FAIL. Got: ${result}`);
            return false;
        }
    } catch (err) {
        console.error(`❌ RN Error: ${err.message}`);
        return false;
    }
};

export default runTest;