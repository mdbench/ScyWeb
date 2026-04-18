const fs = require('fs');
const zlib = require('zlib');

class ScyKernel {
    constructor(password, filePath) {
        this.password = password;
        this.filePath = filePath;
        this.canvasSize = 4000;
        this.hVal = this._getHVal(password);
        this.dbBuffer = null;
    }

    _getHVal(pwd) {
        let hash;
        hash = 7;
        for (let i = 0; i < pwd.length; i++) {
            hash = (Math.imul(hash, 31) + pwd.charCodeAt(i)) | 0;
        }
        let unsignedHash;
        unsignedHash = hash >>> 0;
        let normalized;
        normalized = unsignedHash / 4294967296.0;
        let result;
        result = Math.floor(normalized * 16000000.0);
        return result;
    }

    // Deterministic FNV-1a + Alphabet Salt for Parity with option
    // to support password protected databasing
    _deriveIndex(key, password) {
        let hash;
        hash = 0x811c9dc5 >>> 0;
        let prime;
        prime = 0x01000193;
        let alphaSalt;
        alphaSalt = 0;
        if (password && password.length > 0) {
            for (let i = 0; i < password.length; i++) {
                let pChar;
                pChar = password.charCodeAt(i) & 0xFF;
                hash = (hash ^ pChar) >>> 0;
                hash = Math.imul(hash, prime) >>> 0;
            }
        }
        for (let i = 0; i < key.length; i++) {
            let kCharCode;
            kCharCode = key.charCodeAt(i);
            hash = (hash ^ (kCharCode & 0xFF)) >>> 0;
            hash = Math.imul(hash, prime) >>> 0;
            let c;
            c = key[i];
            if (/[a-zA-Z]/.test(c)) {
                alphaSalt += (c.toLowerCase().charCodeAt(0) - 97 + 1);
            }
        }
        let finalVal;
        finalVal = (hash + alphaSalt) >>> 0;
        let normalized;
        normalized = finalVal / 4294967296.0;
        let result;
        result = Math.floor(normalized * 16000000.0);
        return result;
    }

    _d2xy(n, d) {
        let rx;
        let ry;
        let s;
        let t;
        t = d;
        let x;
        x = 0;
        let y;
        y = 0;
        for (s = 1; s < n; s *= 2) {
            rx = 1 & (Math.floor(t / 2));
            ry = 1 & (t ^ rx);
            let rotated;
            rotated = this._rot(s, x, y, rx, ry);
            x = rotated.x;
            y = rotated.y;
            x = x + (s * rx);
            y = y + (s * ry);
            t = Math.floor(t / 4);
        }
        return { x, y };
    }
    
    _rot(n, x, y, rx, ry) {
        let targetX;
        targetX = x;
        let targetY;
        targetY = y;
        if (ry === 0) {
            if (rx === 1) {
                targetX = n - 1 - targetX;
                targetY = n - 1 - targetY;
            }
            let temp;
            temp = targetX;
            targetX = targetY;
            targetY = temp;
        }
        return { x: targetX, y: targetY };
    }

    /**
     * A bit-perfect, zero-byte overhead encryption layer.
     * XORs the character based on the password's hash and the character's position.
     */
    _cryptByte(c, password, position) {
        let salt;
        salt = 0x811c9dc5 >>> 0;
        let prime;
        prime = 16777619;
        for (let i = 0; i < password.length; i++) {
            let charByte;
            charByte = password.charCodeAt(i) & 0xFF;
            salt = Math.imul(salt ^ charByte, prime) >>> 0;
        }
        let posMult;
        posMult = Math.imul(position, 0xdeadbeef) >>> 0;
        let mixed;
        mixed = (salt ^ posMult) >>> 0;
        mixed ^= (mixed >>> 16);
        let keyByte;
        keyByte = mixed & 0xFF;
        let result;
        result = (c & 0xFF) ^ (keyByte & 0xFF);
        return result & 0xFF;
    }

    // Lightweight CRC-32 for PNG Chunk Compliance
    _computeCRC(buf, len) {
        let crc = 0xffffffff >>> 0;
        for (let i = 0; i < len; i++) {
            crc ^= buf[i];
            for (let j = 0; j < 8; j++) {
                // Using -(crc & 1) logic via bitwise mask
                if (crc & 1) {
                    crc = (crc >>> 1) ^ 0xedb88320;
                } else {
                    crc = crc >>> 1;
                }
            }
        }
        return (crc ^ 0xffffffff) >>> 0;
    }

    _write32(val) {
        const buf = Buffer.alloc(4);
        buf.writeUInt32BE(val, 0);
        return buf;
    }

    // PPM sow, harvest functions
    _putToPPM(key, value, password) {
        const index = this._deriveIndex(key, password);
        const curD = this.hVal + (index * 1600);
        const { x, y } = this._d2xy(this.canvasSize, curD);
        try {
            const fd = fs.openSync(this.filePath, 'r+');
            // Header offset (Standard P6 PPM is 15 bytes)
            let offset = 15 + (y * this.canvasSize + x) * 3;
            for (let i = 0; i < value.length; i++) {
                const pixel = Buffer.alloc(3);
                // Read 3 bytes (the current pixel)
                fs.readSync(fd, pixel, 0, 3, offset);
                // Apply ScyKernel stream cipher
                const charCode = value.charCodeAt(i);
                const secureByte = this._cryptByte(charCode, password, i);
                // Update Red channel
                pixel[0] = secureByte;
                // Overwrite the same pixel
                fs.writeSync(fd, pixel, 0, 3, offset);
                // Advance offset by 3 bytes (1 pixel)
                offset += 3;
            }
            // Write Null Terminator (Red channel = 0)
            const term = Buffer.from([0, 0, 0]);
            fs.writeSync(fd, term, 0, 3, offset);
            fs.closeSync(fd);
        } catch (err) {
            // console.error(`❌ PPM Write Error: ${err.message}`);
        }
    }

    _getFromPPM(key, password) {
        const index = this._deriveIndex(key, password);
        const curD = this.hVal + (index * 1600);
        const { x, y } = this._d2xy(this.canvasSize, curD);
        try {
            const fd = fs.openSync(this.filePath, 'r');
            let offset = 15 + (y * this.canvasSize + x) * 3;
            let result = "";
            let i = 0;
            while (true) {
                const pixel = Buffer.alloc(3);
                const bytesRead = fs.readSync(fd, pixel, 0, 3, offset);
                // Bounds check: Stop if EOF or Red channel is 0 (Null Terminator)
                if (bytesRead < 3 || pixel[0] === 0) {
                    break;
                }
                const scrambled = pixel[0];
                const decryptedByte = this._cryptByte(scrambled, password, i);
                result += String.fromCharCode(decryptedByte);
                offset += 3;
                i++;
            }
            fs.closeSync(fd);
            return result;
        } catch (err) {
            return "";
        }
    }

    // PNG sow, harvest functions
    /**
    * Writes a value to the RAM buffer.
    * Note: You MUST call syncPNG(file, "commit") after calling this to save changes.
    */
    _putToPNG(key, value, keyPassword) {
        // Safety check: ensure buffer is initialized
        if (!this.dbBuffer || this.dbBuffer.length === 0) {
            this.dbBuffer = Buffer.alloc(48000000, 0);
        }
        const index = this._deriveIndex(key, keyPassword);
        const curD = this.hVal + (index * 1600);
        const { x, y } = this._d2xy(this.canvasSize, curD);
        // Linear pixel walk in RAM
        for (let i = 0; i < value.length; i++) {
            const pixelIdx = ((y * this.canvasSize) + (x + i)) * 3;
            if (pixelIdx + 2 < this.dbBuffer.length) {
                // Char code retrieval for bitwise XOR
                const charCode = value.charCodeAt(i);
                const secureByte = this._cryptByte(charCode, keyPassword, i);
                // XOR into Red Channel (Bit-perfect data preservation)
                this.dbBuffer[pixelIdx] = secureByte;
            }
        }
        // Write Null Terminator (0 in Red channel marks the end)
        const termIdx = ((y * this.canvasSize) + (x + value.length)) * 3;
        if (termIdx + 2 < this.dbBuffer.length) {
            this.dbBuffer[termIdx] = 0;
        }
    }

    /**
     * Retrieves a value from the RAM buffer.
     * Note: You SHOULD call _syncPNG(file, "load") before this to ensure fresh data.
     */
    _getFromPNG(key, keyPassword) {
        if (!this.dbBuffer || this.dbBuffer.length === 0) return "";
        const index = this._deriveIndex(key, keyPassword);
        const curD = this.hVal + (index * 1600);
        const { x, y } = this._d2xy(this.canvasSize, curD);
        let result = "";
        let i = 0;
        while (true) {
            const pixelIdx = ((y * this.canvasSize) + (x + i)) * 3;
            // Bounds check + Null Terminator check (Red == 0)
            if (pixelIdx + 2 >= this.dbBuffer.length || this.dbBuffer[pixelIdx] === 0) {
                break;
            }
            const scrambled = this.dbBuffer[pixelIdx];
            const decryptedByte = this._cryptByte(scrambled, keyPassword, i);
            result += String.fromCharCode(decryptedByte);
            i++;
        }
        return result;
    }

    // DB sync functions for easier DB handling
    _syncPNG(filename, mode) {
        mode = mode.toLowerCase();
        // Check if we are in LOAD MODE but the file is missing
        if (mode === "load" && !fs.existsSync(filename)) {
            console.log("⚠️ Database not found. Initializing new compressed store...");
            this.dbBuffer = Buffer.alloc(48000000, 0);
            return this._syncPNG(filename, "commit");
        }
        if (mode === "commit") { // COMMIT MODE (RAM -> Disk)
            const filtered = Buffer.alloc(48004000);
            for (let r = 0; r < 4000; r++) {
                filtered[r * 12001] = 0; // Filter byte
                this.dbBuffer.copy(filtered, r * 12001 + 1, r * 12000, (r + 1) * 12000);
            }
            const compressed = zlib.deflateSync(filtered, { level: 9 });
            try {
                const fd = fs.openSync(filename, 'w');   
                const sig = Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]);
                fs.writeSync(fd, sig);
                const ihdrData = Buffer.from([
                    0x49, 0x48, 0x44, 0x52, 
                    0x00, 0x00, 0x0F, 0xA0,
                    0x00, 0x00, 0x0F, 0xA0,
                    0x08, 0x02, 0x00, 0x00, 0x00 
                ]);
                fs.writeSync(fd, this._write32(13));
                fs.writeSync(fd, ihdrData);
                fs.writeSync(fd, this._write32(this._computeCRC(ihdrData, 17)));
                const idatHeader = Buffer.from("IDAT");
                fs.writeSync(fd, this._write32(compressed.length));
                fs.writeSync(fd, idatHeader);
                fs.writeSync(fd, compressed);
                const idatCrc = this._computeCRC(Buffer.concat([idatHeader, compressed]), compressed.length + 4);
                fs.writeSync(fd, this._write32(idatCrc));
                const iendData = Buffer.from("IEND");
                fs.writeSync(fd, this._write32(0));
                fs.writeSync(fd, iendData);
                fs.writeSync(fd, this._write32(this._computeCRC(iendData, 4)));
                fs.closeSync(fd);
                console.log(`✅ PNG Commit Successful: ${filename}`);
                return true;
            } catch (err) {
                return false;
            }

        } else if (mode === "load") { // LOAD MODE (Disk -> RAM)
            try {
                const file = fs.readFileSync(filename);
                const cLen = file.readUInt32BE(33);
                const cData = file.subarray(41, 41 + cLen);
                const decomp = zlib.inflateSync(cData);
                this.dbBuffer = Buffer.alloc(48000000);
                for (let r = 0; r < 4000; r++) {
                    decomp.copy(this.dbBuffer, r * 12000, r * 12001 + 1, (r + 1) * 12001);
                }
                //console.log(`✅ PNG Load Successful: ${filename}`);
                return true;
            } catch (err) {
                return false;
            }
        }
        return false;
    }

    _syncPPM(filename, mode) {
        mode = mode.toLowerCase();
        // Check if we are in LOAD MODE but the file is missing
        if (mode === "load" && !fs.existsSync(filename)) {
            console.log("⚠️ PPM Database not found. Initializing new raw store...");
            this.dbBuffer = Buffer.alloc(48000000, 0);
            return this._syncPPM(filename, "commit");
        }
        if (mode === "commit") { // COMMIT MODE (RAM -> Disk)
            try {
                const header = `P6\n4000 4000\n255\n`;
                const output = Buffer.concat([Buffer.from(header), this.dbBuffer]);
                fs.writeFileSync(filename, output);
                console.log(`✅ PPM Commit Successful: ${filename}`);
                return true;
            } catch (err) {
                return false;
            }
        } else if (mode === "load") { // LOAD MODE (Disk -> RAM)
            try {
                const file = fs.readFileSync(filename);
                // PPM header "P6\n4000 4000\n255\n" is exactly 15 bytes
                this.dbBuffer = file.subarray(15, 15 + 48000000);
                console.log(`✅ PPM Load Successful: ${filename}`);
                return true;
            } catch (err) {
                return false;
            }
        }
        return false;
    }

    // Blank DB creation functions
    _createPNG_DB(filename) {
        this.dbBuffer = Buffer.alloc(48000000, 0);
        if (this._syncPNG(filename, "commit")) {
            console.log(`✅ PNG initialized and loaded into buffer: ${filename}`);
        } else {
            console.error("❌ Failed to initialize PNG database file.");
        }
    }

    _createPPM_DB(dbPath) {
        try {
            const fd = fs.openSync(dbPath, 'w');
            // Write the P6 Header (Standard 4000x4000 8-bit RGB)
            const header = `P6\n${this.canvasSize} ${this.canvasSize}\n255\n`;
            fs.writeSync(fd, header);
            // Create one row of zeros (4000 pixels * 3 bytes)
            const zeroRow = Buffer.alloc(this.canvasSize * 3, 0);
            for (let i = 0; i < this.canvasSize; i++) {
                fs.writeSync(fd, zeroRow);
            }
            fs.closeSync(fd);
            console.log(`✅ PPM Database Ready (Isolated from RAM): ${dbPath}`);
        } catch (err) {
            console.error(`❌ Error: Could not create PPM database: ${err.message}`);
        }
    }

    // DB conversion functions
    _convertDatabaseFormat(pngPath, ppmPath, targetFormat) {
        // Standardize the flag to lowercase
        const format = targetFormat.toLowerCase();
        if (format === "ppm") {
            // SOURCE: PNG -> TARGET: PPM (Decompress and Expand)
            if (!this._syncPNG(pngPath, "load")) {
                console.error("❌ Failed to load PNG database.");
                return false;
            }
            try {
                // Create the PPM Header
                const header = Buffer.from("P6\n4000 4000\n255\n");
                // Concatenate header and the raw buffer
                const output = Buffer.concat([header, this.dbBuffer]);   
                fs.writeFileSync(ppmPath, output);
                console.log("✅ Converted PNG to PPM (48MB Raw Volume)");
                return true;
            } catch (err) {
                return false;
            }
        } else if (format === "png") {
            // SOURCE: PPM -> TARGET: PNG (Pack and Compress)
            try {
                const fullFile = fs.readFileSync(ppmPath);
                // Skip the header (15 bytes) and extract the raw 48MB
                // subarray() provides a view without copying the memory
                const rawDataSize = 48000000;
                this.dbBuffer = fullFile.subarray(15, 15 + rawDataSize);
                // Use syncPNG to compress and save as a PNG
                if (!this._syncPNG(pngPath, "commit")) {
                    console.error("❌ Failed to compress and save PNG database.");
                    return false;
                }
                console.log("✅ Converted PPM to PNG");
                return true;
            } catch (err) {
                return false;
            }
        } else {
            console.error("❌ Invalid target format. Use 'PNG' or 'PPM'.");
            return false;
        }
    }

    // DB Deletion and cleanup functions
    _deleteDB(dbPath) {
        try {
            fs.unlinkSync(dbPath); // Synchronous, no callback needed
            return true;
        } catch (error) {
            if (error.code === 'ENOENT') return false;
            throw error;
        }
    }

    // DB checking/validating functions
    _getFileSize(path) {
        try {
            // Check if path exists and is a regular file
            const stats = fs.statSync(path);
            if (stats.isFile()) {
                return stats.size;
            }
        } catch (err) {
            // console.error(`❌ Filesystem Error: ${err.message}`);
        }
        return 0;
    }

    _validateDB(path) {
        // 4000 * 4000 * 3
        const rawDataSize = 48000000;
        const actual = this._getFileSize(path);
        if (path.includes(".ppm")) {
            // PPM must have the header + the data (Header is ~15 bytes)
            return actual >= (rawDataSize + 15);
        } else {
            // PNG/Raw must be at least the data size
            return actual >= rawDataSize;
        }
    }

}

module.exports = ScyKernel;