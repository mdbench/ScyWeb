import RNFS from 'react-native-fs';
import { Buffer } from 'buffer'; // Use the 'buffer' polyfill for RN

class ScyKernel {

    constructor(password, filePath) {
        this.password = password;
        this.filePath = filePath;
        this.canvasSize = 4000;
        this.pixelDataSize = 48000000;
        this.hVal = this.getHVal(password);
        this.dbBuffer = new Uint8Array(0);
    }

    getHVal(pwd) {
        let hash = 7;
        for (let i = 0; i < pwd.length; i++) {
            hash = Math.imul(hash, 31) + pwd.charCodeAt(i) >>> 0;
        }
        let normalized = hash / 4294967296.0;
        return Math.floor(normalized * 16000000.0) >>> 0;
    }

    deriveIndex(key, password) {
        let hash = 0x811c9dc5 >>> 0;
        let prime = 0x01000193;
        let alphaSalt = 0;
        if (password.length > 0) {
            for (let i = 0; i < password.length; i++) {
                hash ^= password.charCodeAt(i);
                hash = Math.imul(hash, prime) >>> 0;
            }
        }
        for (let i = 0; i < key.length; i++) {
            let b = key.charCodeAt(i);
            hash ^= b;
            hash = Math.imul(hash, prime) >>> 0;
            if (/[a-zA-Z]/.test(key[i])) {
                alphaSalt += (key[i].toLowerCase().charCodeAt(0) - 97 + 1);
            }
        }
        let finalVal = (hash + alphaSalt) >>> 0;
        let normalized = finalVal / 4294967296.0;
        return Math.floor(normalized * 16000000.0);
    }

    d2xy(n, d) {
        let x = 0, y = 0, t = d;
        for (let s = 1; s < n; s *= 2) {
            let rx = 1 & (Math.floor(t / 2));
            let ry = 1 & (t ^ rx);
            let pts = this.rot(s, x, y, rx, ry);
            x = pts.x + s * rx;
            y = pts.y + s * ry;
            t = Math.floor(t / 4);
        }
        return { x, y };
    }

    rot(n, x, y, rx, ry) {
        if (ry === 0) {
            if (rx === 1) {
                x = n - 1 - x;
                y = n - 1 - y;
            }
            return { x: y, y: x };
        }
        return { x, y };
    }

    cryptByte(c, password, position) {
        let salt = 0x811c9dc5 >>> 0;
        for (let i = 0; i < password.length; i++) {
            salt = Math.imul(salt ^ password.charCodeAt(i), 16777619) >>> 0;
        }
        let mixed = (salt ^ (Math.imul(position, 0xdeadbeef) >>> 0)) >>> 0;
        mixed ^= (mixed >>> 16);
        let keyByte = mixed & 0xFF;
        return String.fromCharCode(c.charCodeAt(0) ^ keyByte);
    }

    compute_crc(buf) {
        let crc = 0xFFFFFFFF >>> 0;
        for (let i = 0; i < buf.length; i++) {
            crc ^= buf[i];
            for (let j = 0; j < 8; j++) {
                crc = (crc >>> 1) ^ (0xEDB88320 & (-(crc & 1))) >>> 0;
            }
        }
        return (~crc) >>> 0;
    }

    write32(val) {
        let b = new Uint8Array(4);
        b[0] = (val >> 24) & 0xFF;
        b[1] = (val >> 16) & 0xFF;
        b[2] = (val >> 8) & 0xFF;
        b[3] = val & 0xFF;
        return b;
    }

    // PPM sow, harvest functions
    async putToPPM(key, value, password) {
        const index = this.deriveIndex(key, password);
        const curD = this.hVal + (index * 1600);
        const { x, y } = this.d2xy(this.canvasSize, curD);
        try {
            const offset = 15 + (y * this.canvasSize + x) * 3;
            for (let i = 0; i < value.length; i++) {
                const pixelHex = await RNFS.read(this.filePath, 3, offset + (i * 3), 'base64');
                let pixel = Buffer.from(pixelHex, 'base64');
                const secureChar = this.cryptByte(value[i], password, i);
                pixel[0] = secureChar.charCodeAt(0) & 0xFF;
                await RNFS.write(this.filePath, pixel.toString('base64'), offset + (i * 3), 'base64');
            }
            const term = Buffer.from([0, 0, 0]).toString('base64');
            await RNFS.write(this.filePath, term, offset + (value.length * 3), 'base64');
        } catch (e) {
            return;
        }
    }

    async getFromPPM(key, password) {
        const index = this.deriveIndex(key, password);
        const curD = this.hVal + (index * 1600);
        const { x, y } = this.d2xy(this.canvasSize, curD);
        try {
            let result = "";
            let i = 0;
            const startOffset = 15 + (y * this.canvasSize + x) * 3;
            while (true) {
                const pixelHex = await RNFS.read(this.filePath, 3, startOffset + (i * 3), 'base64');
                const pixel = Buffer.from(pixelHex, 'base64');
                if (pixel.length === 0 || pixel[0] === 0) break;
                const scrambled = String.fromCharCode(pixel[0]);
                result += this.cryptByte(scrambled, password, i);
                i++;
            }
            return result;
        } catch (e) {
            return "";
        }
    }

    // PNG sow, harvest functions
    /**
    * Writes a value to the RAM buffer.
    * Note: You MUST call syncPNG(file, "commit") after calling this to save changes.
    */
    putToPNG(key, value, keyPassword) {
        if (this.dbBuffer.length === 0) this.dbBuffer = new Uint8Array(48000000).fill(0);
        const index = this.deriveIndex(key, keyPassword);
        const curD = this.hVal + (index * 1600);
        const { x, y } = this.d2xy(this.canvasSize, curD);
        for (let i = 0; i < value.length; i++) {
            const pixelIdx = ((y * this.canvasSize) + (x + i)) * 3;
            if (pixelIdx + 2 < this.dbBuffer.length) {
                const secureChar = this.cryptByte(value[i], keyPassword, i);
                this.dbBuffer[pixelIdx] = secureChar.charCodeAt(0) & 0xFF;
            }
        }
        const termIdx = ((y * this.canvasSize) + (x + value.length)) * 3;
        if (termIdx + 2 < this.dbBuffer.length) {
            this.dbBuffer[termIdx] = 0;
        }
    }

    getFromPNG(key, keyPassword) {
        if (this.dbBuffer.length === 0) return "";
        const index = this.deriveIndex(key, keyPassword);
        const curD = this.hVal + (index * 1600);
        const { x, y } = this.d2xy(this.canvasSize, curD);
        let result = "";
        let i = 0;
        while (true) {
            const pixelIdx = ((y * this.canvasSize) + (x + i)) * 3;
            if (pixelIdx + 2 >= this.dbBuffer.length || this.dbBuffer[pixelIdx] === 0) {
                break;
            }
            const scrambled = String.fromCharCode(this.dbBuffer[pixelIdx]);
            result += this.cryptByte(scrambled, keyPassword, i);
            i++;
        }
        return result;
    }

    // DB sync functions for easier DB handling
    async syncPNG(filename, mode) {
        mode = mode.toLowerCase();
        if (mode === "load" && !await RNFS.exists(filename)) {
            this.dbBuffer = new Uint8Array(48000000).fill(0);
            return await this.syncPNG(filename, "commit");
        }
        if (mode === "commit") {
            let filtered = new Uint8Array(48004000);
            for (let r = 0; r < 4000; r++) {
                filtered[r * 12001] = 0;
                filtered.set(this.dbBuffer.subarray(r * 12000, (r + 1) * 12000), r * 12001 + 1);
            }
            const compressed = pako.deflate(filtered);
            const sig = new Uint8Array([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]);
            const ihdrData = new Uint8Array([73, 72, 68, 82, 0, 0, 15, 160, 0, 0, 15, 160, 8, 2, 0, 0, 0]);
            const ihdrCRC = this.write32(this.compute_crc(ihdrData));
            const idatLen = this.write32(compressed.length);
            const idatTag = new Uint8Array([73, 68, 65, 84]);
            const crcB = new Uint8Array(idatTag.length + compressed.length);
            crcB.set(idatTag);
            crcB.set(compressed, 4);
            const idatCRC = this.write32(this.compute_crc(crcB));
            const iendData = new Uint8Array([0, 0, 0, 0, 73, 69, 78, 68, 174, 66, 96, 130]);
            const totalSize = sig.length + 4 + ihdrData.length + 4 + 4 + 4 + compressed.length + 4 + iendData.length;
            const out = new Uint8Array(totalSize);
            let offset = 0;
            out.set(sig, offset); offset += sig.length;
            out.set(this.write32(13), offset); offset += 4;
            out.set(ihdrData, offset); offset += ihdrData.length;
            out.set(ihdrCRC, offset); offset += 4;
            out.set(idatLen, offset); offset += 4;
            out.set(idatTag, offset); offset += 4;
            out.set(compressed, offset); offset += compressed.length;
            out.set(idatCRC, offset); offset += 4;
            out.set(iendData, offset);
            await RNFS.writeFile(filename, Buffer.from(out).toString('base64'), 'base64');
            return true;
        } else if (mode === "load") {
            const b64 = await RNFS.readFile(filename, 'base64');
            const fileData = Buffer.from(b64, 'base64');
            const cLen = (fileData[33] << 24 | fileData[34] << 16 | fileData[35] << 8 | fileData[36]) >>> 0;
            const cData = fileData.slice(41, 41 + cLen);
            const decomp = pako.inflate(cData);
            this.dbBuffer = new Uint8Array(48000000);
            for (let r = 0; r < 4000; r++) {
                this.dbBuffer.set(decomp.subarray(r * 12001 + 1, r * 12001 + 12001), r * 12000);
            }
            return true;
        }
        return false;
    }

    async syncPPM(filename, mode) {
        mode = mode.toLowerCase();
        if (mode === "load" && !await RNFS.exists(filename)) {
            this.dbBuffer = new Uint8Array(48000000).fill(0);
            return await this.syncPPM(filename, "commit");
        }
        if (mode === "commit") {
            const header = "P6\n4000 4000\n255\n";
            const headerBytes = Buffer.from(header);
            const out = new Uint8Array(headerBytes.length + this.dbBuffer.length);
            out.set(headerBytes, 0);
            out.set(this.dbBuffer, headerBytes.length);
            await RNFS.writeFile(filename, Buffer.from(out).toString('base64'), 'base64');
            return true;
        } else if (mode === "load") {
            const b64 = await RNFS.readFile(filename, 'base64');
            const fileData = Buffer.from(b64, 'base64');
            this.dbBuffer = new Uint8Array(fileData.slice(15, 48000015));
            return true;
        }
        return false;
    }

    // Blank DB creation functions
    async createPNG_DB(filename) {
        this.dbBuffer = new Uint8Array(48000000).fill(0);
        if (await this.syncPNG(filename, "commit")) {
            return true;
        } else {
            return false;
        }
    }

    async createPPM_DB(dbPath) {
        try {
            const header = `P6\n${this.canvasSize} ${this.canvasSize}\n255\n`;
            const rowSize = this.canvasSize * 3;
            const zeroRow = new Uint8Array(rowSize).fill(0);
            const headerBase64 = Buffer.from(header).toString('base64');
            await RNFS.writeFile(dbPath, headerBase64, 'base64');
            const rowBase64 = Buffer.from(zeroRow).toString('base64');
            for (let i = 0; i < this.canvasSize; i++) {
                await RNFS.appendFile(dbPath, rowBase64, 'base64');
            }
            return true;
        } catch (e) {
            return false;
        }
    }

    // DB conversion functions
    async convertDatabaseFormat(pngPath, ppmPath, targetFormat) {
        targetFormat = targetFormat.toLowerCase();
        if (targetFormat === "ppm") {
            if (!await this.syncPNG(pngPath, "load")) {
                return false;
            }
            try {
                const header = "P6\n4000 4000\n255\n";
                const headerBytes = Array.from(header).map(c => c.charCodeAt(0));
                const fullData = new Uint8Array(headerBytes.length + this.dbBuffer.length);
                fullData.set(headerBytes, 0);
                fullData.set(this.dbBuffer, headerBytes.length);
                const base64Data = Buffer.from(fullData).toString('base64');
                await RNFS.writeFile(ppmPath, base64Data, 'base64');
                return true;
            } catch (e) {
                return false;
            }
        } else if (targetFormat === "png") {
            try {
                const base64 = await RNFS.readFile(ppmPath, 'base64');
                const fullBuffer = Buffer.from(base64, 'base64');
                this.dbBuffer = new Uint8Array(fullBuffer.slice(15, 48000015));
                if (!await this.syncPNG(pngPath, "commit")) {
                    return false;
                }
                return true;
            } catch (e) {
                return false;
            }
        } else {
            return false;
        }
    }

    // DB Deletion and cleanup functions
    async deleteDB(path) {
        try {
            const fullPath = path.startsWith('/') ? path : `${RNFS.DocumentDirectoryPath}/${path}`;            
            const exists = await RNFS.exists(fullPath);
            if (exists) {
            await RNFS.unlink(fullPath);
            return true;
            }
            return false;
        } catch (error) {
            console.error("ScyWeb Cleanup Error:", error);
            return false;
        }
    }

    // DB checking/validating functions
    async getFileSize(path) {
        try {
            const exists = await RNFS.exists(path);
            if (exists) {
                const stat = await RNFS.stat(path);
                return stat.size;
            }
        } catch (e) {
            console.error("❌ Filesystem Error: ", e);
        }
        return 0;
    }

    async validateDB(path) {
        const rawDataSize = 48000000;
        const actual = await this.getFileSize(path);
        if (path.toLowerCase().endsWith(".ppm")) {
            return actual >= (rawDataSize + 15);
        } else {
            return actual >= 1000;
        }
    }

}

export default ScyKernel;