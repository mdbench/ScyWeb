import RNFS from 'react-native-fs';
import { Buffer } from 'buffer'; // Use the 'buffer' polyfill for RN

class ScyKernel {
    constructor(password, filePath) {
        this.password = password;
        this.filePath = filePath;
        this.canvasSize = 4000;
        this.hVal = this._getHVal(password);
    }

    _getHVal(pwd) {
        let hash = 7;
        for (let i = 0; i < pwd.length; i++) {
            hash = (hash * 31 + pwd.charCodeAt(i)) | 0;
        }
        // Vectorial Normalization: (Unsigned 32-bit / 2^32) * 16M
        const unsignedHash = hash >>> 0;
        return Math.floor((unsignedHash / 4294967296.0) * 16000000);
    }

    // Deterministic FNV-1a + Alphabet Salt for Cross-Language Parity
    _deriveIndex(key, password) {
        let hash = 0x811c9dc5 | 0; // Force signed 32-bit
        const prime = 0x01000193;
        let alphaSalt = 0;
    
        const encoder = new TextEncoder();
    
        const passBytes = encoder.encode(password);
        for (let b of passBytes) {
          hash ^= b;
          hash = Math.imul(hash, prime);
        }
    
        const keyBytes = encoder.encode(key);
        for (let b of keyBytes) {
          hash ^= b;
          hash = Math.imul(hash, prime);
    
          const char = String.fromCharCode(b);
          if (/[a-zA-Z]/.test(char)) {
            alphaSalt += (char.toLowerCase().charCodeAt(0) - 'a'.charCodeAt(0) + 1);
          }
        }
    
        const unsignedHash = hash >>> 0;
        const finalVal = (unsignedHash + alphaSalt) >>> 0;
        
        const normalized = (finalVal / 4294967296.0) * 16000000.0;
        return Math.floor(normalized);
    }

    _rot(n, x, y, rx, ry) {
        if (ry === 0) {
            if (rx === 1) {
                x = n - 1 - x;
                y = n - 1 - y;
            }
            return [y, x];
        }
        return [x, y];
    }

    _d2xy(n, d) {
        let x = 0, y = 0, t = d;
        for (let s = 1; s < n; s *= 2) {
            const rx = 1 & (Math.floor(t / 2));
            const ry = 1 & (t ^ rx);
            [x, y] = this._rot(s, x, y, rx, ry);
            x += s * rx;
            y += s * ry;
            t = Math.floor(t / 4);
        }
        return [x, y];
    }

    async put(key, value, password) {
        const index = this._deriveIndex(key, password);
        const curD = this.hVal + (index * 1600);
        const [x, y] = this._d2xy(this.canvasSize, curD);

        const offset = 15 + (y * this.canvasSize + x) * 3;
        const data = Buffer.from(value, 'utf8');

        for (let i = 0; i < data.length; i++) {
            const pixelPos = offset + (i * 3);
            // Read 3 bytes (one pixel)
            const base64Pixel = await RNFS.read(this.filePath, 3, pixelPos, 'base64');
            const pixel = Buffer.from(base64Pixel, 'base64');
            
            // XOR Obfuscation
            pixel[0] ^= data[i];
            
            // Write back
            await RNFS.write(this.filePath, pixel.toString('base64'), pixelPos, 'base64');
        }

        // Null Terminator
        const term = Buffer.from([0, 0, 0]);
        await RNFS.write(this.filePath, term.toString('base64'), offset + (data.length * 3), 'base64');
    }

    async get(key, password) {
        const index = this._deriveIndex(key, password);
        const curD = this.hVal + (index * 1600);
        const [x, y] = this._d2xy(this.canvasSize, curD);

        const offset = 15 + (y * this.canvasSize + x) * 3;
        const resultBytes = [];

        let i = 0;
        while (true) {
            const pixelPos = offset + (i * 3);
            const base64Pixel = await RNFS.read(this.filePath, 3, pixelPos, 'base64');
            const pixel = Buffer.from(base64Pixel, 'base64');
            
            if (pixel.length === 0 || pixel[0] === 0) break;
            resultBytes.push(pixel[0]);
            i++;
        }

        return Buffer.from(resultBytes).toString('utf8');
    }

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

}

export default ScyKernel;