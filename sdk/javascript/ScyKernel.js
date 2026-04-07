const fs = require('fs');

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
            // Force 32-bit integer parity with C++
            hash = (Math.imul(hash, 31) + pwd.charCodeAt(i)) | 0;
        }
        const unsignedHash = hash >>> 0;
        // Vectorial Normalization: (Unsigned 32-bit / 2^32) * 16M
        return Math.floor((unsignedHash / 4294967296.0) * 16000000);
    }

    // Deterministic FNV-1a + Alphabet Salt for Parity
    _deriveIndex(key) {
        let hash = 0x811c9dc5 >>> 0;
        const prime = 0x01000193;
        let alphaSalt = 0;

        const lowerKey = key.toLowerCase();
        for (let i = 0; i < key.length; i++) {
            hash ^= key.charCodeAt(i);
            hash = Math.imul(hash, prime) >>> 0;

            if (/[a-z]/.test(lowerKey[i])) {
                // Parity fix: 'a' should be 1 (charCode 97 - 96)
                alphaSalt += (lowerKey.charCodeAt(i) - 97 + 1);
            }
        }
        // Combine hash and salt, clamp to 32-bit unsigned, and project
        const finalVal = (hash + alphaSalt) >>> 0;
        return Math.floor((finalVal / 4294967296.0) * 16000000);
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
        // s starts at 1 and doubles each iteration (1, 2, 4, 8...)
        for (let s = 1; s < n; s *= 2) {
            const rx = 1 & (Math.floor(t / 2));
            const ry = 1 & (t ^ rx);
            
            // pass 's' (current quadrant size), not 'n'
            const [nx, ny] = this._rot(s, x, y, rx, ry);
            x = nx + s * rx;
            y = ny + s * ry;
            
            t = Math.floor(t / 4);
        }
        return [x, y];
    }

    put(key, value) {
        const index = this._deriveIndex(key);
        const curD = this.hVal + (index * 1600);
        const [x, y] = this._d2xy(this.canvasSize, curD);

        const fd = fs.openSync(this.filePath, 'r+');
        const offset = 15 + (y * this.canvasSize + x) * 3;
        const data = Buffer.from(value, 'utf8');

        for (let i = 0; i < data.length; i++) {
            const pixel = Buffer.alloc(3);
            fs.readSync(fd, pixel, 0, 3, offset + (i * 3));
            
            // XOR Obfuscation
            pixel[0] ^= data[i];
            
            fs.writeSync(fd, pixel, 0, 3, offset + (i * 3));
        }

        // Null Terminator
        fs.writeSync(fd, Buffer.from([0, 0, 0]), 0, 3, offset + (data.length * 3));
        fs.closeSync(fd);
    }

    get(key) {
        const index = this._deriveIndex(key);
        const curD = this.hVal + (index * 1600);
        const [x, y] = this._d2xy(this.canvasSize, curD);

        const fd = fs.openSync(this.filePath, 'r');
        const offset = 15 + (y * this.canvasSize + x) * 3;
        const resultBytes = [];

        let i = 0;
        while (true) {
            const pixel = Buffer.alloc(3);
            const bytesRead = fs.readSync(fd, pixel, 0, 3, offset + (i * 3));
            if (bytesRead === 0 || pixel[0] === 0) break;
            resultBytes.push(pixel[0]);
            i++;
        }

        fs.closeSync(fd);
        return Buffer.from(resultBytes).toString('utf8');
    }
}

module.exports = ScyKernel;