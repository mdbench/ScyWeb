#ifndef SCY_KERNEL_HPP
#define SCY_KERNEL_HPP

#include <iostream>
#include <string>
#include <vector>
#include <fstream>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <algorithm>
#include <zlib.h> // Link with -lz

class ScyKernel {
private:
    std::string password;
    std::string filePath;
    int hVal;
    const int canvasSize = 4000;
    const size_t pixelDataSize = 48000000;
    std::vector<uint8_t> dbBuffer;

    // Deterministic FNV-1a Hash + Alphabet Salt
    int deriveIndex(const std::string& key, const std::string& password) {
        uint32_t hash = 0x811c9dc5; // FNV offset basis
        uint32_t prime = 0x01000193; // FNV prime
        long alphaSalt = 0;

        if (!password.empty()) {
            for (char c : password) {
                hash ^= (uint8_t)c;
                hash *= prime;
            }
        }

        for (char c : key) {
            // FNV-1a Math
            hash ^= (uint8_t)c;
            hash *= prime;
            // Alphabet Salt Math (A=1, B=2...)
            if (std::isalpha(static_cast<unsigned char>(c))) {
                alphaSalt += (std::tolower(static_cast<unsigned char>(c)) - 'a' + 1);
            }
        }
        // Combine, truncate to 32-bit unsigned, then project
        uint32_t finalVal = static_cast<uint32_t>(static_cast<long>(hash) + alphaSalt);
        double normalized = (static_cast<double>(finalVal) / 4294967296.0) * 16000000.0;
        return static_cast<int>(std::floor(normalized));
    }

    void d2xy(int n, int d, int &x, int &y) {
        int rx, ry, s, t = d;
        x = y = 0;
        for (s = 1; s < n; s *= 2) {
            rx = 1 & (t / 2);
            ry = 1 & (t ^ rx);
            rot(s, x, y, rx, ry);
            x += s * rx;
            y += s * ry;
            t /= 4;
        }
    }

    void rot(int n, int &x, int &y, int rx, int ry) {
        if (ry == 0) {
            if (rx == 1) {
                x = n - 1 - x;
                y = n - 1 - y;
            }
            std::swap(x, y);
        }
    }

    int getHVal(const std::string& pwd) {
        uint32_t hash = 7;
        for (char c : pwd) {
            hash = (hash * 31) + (uint8_t)c;
        }
        // Project onto the 16M canvas
        double normalized = (static_cast<double>(hash) / 4294967296.0) * 16000000.0;
        return static_cast<int>(std::floor(normalized));
    }

    /**
    * A bit-perfect, zero-byte overhead encryption layer.
    * XORs the character based on the password's hash and the character's position.
    */
    char cryptByte(char c, const std::string& password, int position) {
        // Generate a deterministic 'Salt' from the password
        // Using a prime-base (31) multiplier for a simple hash distribution
        uint32_t salt = 0x811c9dc5; // FNV offset basis or similar starting seed
        for (char pc : password) {
            salt = (salt ^ (uint8_t)pc) * 16777619; // FNV-1a style mixing
        }
        
        // Derive a unique keyByte for this specific pixel/character position
        // position * 0xdeadbeef ensures the keystream doesn't repeat for common patterns
        uint32_t mixed = salt ^ (static_cast<uint32_t>(position) * 0xdeadbeef);
        
        // Final mixing to ensure the byte-tap is high-entropy
        mixed ^= (mixed >> 16);
        uint8_t keyByte = (uint8_t)(mixed & 0xFF);
        
        // XOR Transformation
        return c ^ keyByte;
    }

    // Lightweight CRC-32 for PNG Chunk Compliance
    uint32_t compute_crc(const uint8_t* buf, size_t len) {
        uint32_t crc = 0xFFFFFFFF;
        for (size_t i = 0; i < len; i++) {
            crc ^= buf[i];
            for (int j = 0; j < 8; j++) {
                crc = (crc >> 1) ^ (0xEDB88320 & (-(crc & 1)));
            }
        }
        return ~crc;
    }

    void write32(std::ostream& out, uint32_t val) {
        uint8_t b[] = {(uint8_t)(val >> 24), (uint8_t)(val >> 16), (uint8_t)(val >> 8), (uint8_t)val};
        out.write((char*)b, 4);
    }

public:
    ScyKernel(std::string pwd, std::string path) : password(pwd), filePath(path) {
        hVal = getHVal(pwd);
        dbBuffer.assign(canvasSize * canvasSize * 3, 0);
    }

    // PPM sow, harvest functions
    void putToPPM(const std::string& key, const std::string& value, const std::string& password) {
        int index = deriveIndex(key, password);
        int curD = hVal + (index * 1600);
        int x, y;
        d2xy(canvasSize, curD, x, y);

        std::fstream file(filePath, std::ios::in | std::ios::out | std::ios::binary);
        if (!file) return;

        // Header offset (approx P6 PPM)
        long offset = 15 + (y * canvasSize + x) * 3;
        file.seekp(offset);

        for (char c : value) {
            uint8_t pixel[3];
            // Read 3 bytes (the current pixel)
            file.read((char*)pixel, 3);
            
            pixel[0] ^= (uint8_t)c; // XOR Obfuscation on Red channel
            
            // Move back 3 bytes to overwrite the SAME pixel we just read
            file.seekp(-3, std::ios::cur);
            file.write((char*)pixel, 3);
            
            // Ensure the read pointer is also updated for the next iteration if needed
            file.seekg(file.tellp());
        }
        // Write Null Terminator
        uint8_t term[3] = {0, 0, 0};
        file.write((char*)term, 3);
        file.close();
    }

    std::string getFromPPM(const std::string& key, const std::string& password) {
        int index = deriveIndex(key, password);
        int curD = hVal + (index * 1600);
        int x, y;
        d2xy(canvasSize, curD, x, y);

        std::ifstream file(filePath, std::ios::binary);
        if (!file) return "";

        long offset = 15 + (y * canvasSize + x) * 3;
        file.seekg(offset);

        std::string result = "";
        while (true) {
            uint8_t pixel[3];
            file.read((char*)pixel, 3);
            if (pixel[0] == 0 || file.eof()) break; 
            result += (char)pixel[0];
        }
        file.close();
        return result;
    }

    // PNG sow, harvest functions
    /**
    * Writes a value to the RAM buffer.
    * Note: You MUST call syncDatabase(file, 0) after calling this to save changes.
    */
    void putToPNG(const std::string& key, const std::string& value, const std::string& keyPassword) {
        // Safety check: ensure buffer is initialized
        if (dbBuffer.empty()) dbBuffer.resize(48000000, 0);

        int index = deriveIndex(key, keyPassword);
        int curD = hVal + (index * 1600);
        int x, y;
        d2xy(canvasSize, curD, x, y);

        // Linear pixel walk in RAM
        for (size_t i = 0; i < value.length(); ++i) {
            int pixelIdx = ((y * canvasSize) + (x + i)) * 3;

            if (pixelIdx + 2 < dbBuffer.size()) {
                char secureChar = cryptByte(value[i], keyPassword, (int)i);
                // XOR into Red Channel (Bit-perfect data preservation)
                dbBuffer[pixelIdx] = (uint8_t)secureChar;
            }
        }

        // Write Null Terminator (0 in Red channel marks the end)
        int termIdx = ((y * canvasSize) + (x + value.length())) * 3;
        if (termIdx + 2 < dbBuffer.size()) {
            dbBuffer[termIdx] = 0;
        }
    }

    /**
    * Retrieves a value from the RAM buffer.
    * Note: You SHOULD call syncDatabase(file, 1) before this to ensure fresh data.
    */
    std::string getFromPNG(const std::string& key, const std::string& keyPassword) {
        if (dbBuffer.empty()) return ""; 

        int index = deriveIndex(key, keyPassword);
        int curD = hVal + (index * 1600);
        int x, y;
        d2xy(canvasSize, curD, x, y);

        std::string result = "";
        int i = 0;
        while (true) {
            int pixelIdx = ((y * canvasSize) + (x + i)) * 3;
            
            // Bounds check + Null Terminator check (Red == 0)
            if (pixelIdx + 2 >= dbBuffer.size() || dbBuffer[pixelIdx] == 0) {
                break;
            }

            char scrambled = (char)dbBuffer[pixelIdx];
            result += cryptByte(scrambled, keyPassword, i);
            i++;
        }
        return result;
    }

    bool syncDatabase(const std::string& filename, int mode) {
        // Check if we are in LOAD MODE but the file is missing
        if (mode == 1 && !std::filesystem::exists(filename)) {
            std::cout << "⚠️ Database not found. Initializing new compressed store..." << std::endl;
            // Zero out the buffer and force a COMMIT (mode 0) to create the file
            std::fill(dbBuffer.begin(), dbBuffer.end(), 0);
            return syncDatabase(filename, 0); 
        }

        if (mode == 0) { // COMMIT MODE (RAM -> Disk)
            std::vector<uint8_t> filtered;
            filtered.reserve(48004000);
            for (int r = 0; r < 4000; r++) {
                filtered.push_back(0); 
                filtered.insert(filtered.end(), dbBuffer.begin() + (r * 12000), dbBuffer.begin() + ((r + 1) * 12000));
            }

            uLongf cSize = compressBound(filtered.size());
            std::vector<uint8_t> compressed(cSize);
            if (compress(compressed.data(), &cSize, filtered.data(), filtered.size()) != Z_OK) return false;
            compressed.resize(cSize);

            std::ofstream out(filename, std::ios::binary);
            const uint8_t sig[] = {0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A};
            out.write((char*)sig, 8);
            
            uint8_t ihdr[] = {'I','H','D','R', 0,0,0x0F,0xA0, 0,0,0x0F,0xA0, 8, 2, 0, 0, 0};
            write32(out, 13); out.write((char*)ihdr, 17); write32(out, compute_crc(ihdr, 17));

            write32(out, compressed.size());
            out.write("IDAT", 4); out.write((char*)compressed.data(), compressed.size());
            
            std::vector<uint8_t> crcB = {'I','D','A','T'};
            crcB.insert(crcB.end(), compressed.begin(), compressed.end());
            write32(out, compute_crc(crcB.data(), crcB.size()));

            write32(out, 0); out.write("IEND", 4); write32(out, compute_crc((uint8_t*)"IEND", 4));
            return true;

        } else { // LOAD MODE (Disk -> RAM)
            std::ifstream file(filename, std::ios::binary);
            if (!file) return false;

            file.seekg(33);
            uint32_t cLen;
            char lBuf[4]; file.read(lBuf, 4);
            cLen = (uint8_t(lBuf[0]) << 24) | (uint8_t(lBuf[1]) << 16) | (uint8_t(lBuf[2]) << 8) | uint8_t(lBuf[3]);

            file.seekg(4, std::ios::cur); 
            std::vector<uint8_t> cData(cLen);
            file.read((char*)cData.data(), cLen);

            uLongf uSize = 48004000;
            std::vector<uint8_t> decomp(uSize);
            if (uncompress(decomp.data(), &uSize, cData.data(), cLen) != Z_OK) return false;

            dbBuffer.assign(48000000, 0);
            for (int r = 0; r < 4000; r++) {
                std::copy(decomp.begin() + (r * 12001) + 1, decomp.begin() + (r * 12001) + 12001, dbBuffer.begin() + (r * 12000));
            }
            return true;
        }
    }

    void createPNG_DB(const std::string& filename) {
        std::fill(dbBuffer.begin(), dbBuffer.end(), 0);
        std::ofstream out(filename, std::ios::binary);
        if (!out) return;
        const uint8_t pngSig[] = {0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A};
        out.write(reinterpret_cast<const char*>(pngSig), 8);
        out.close();
        std::cout << "✅ PNG initialized with system signature: " << filename << std::endl;
    }

    void createPPM_DB(const std::string& dbPath) {
        std::ofstream ofs(dbPath, std::ios::binary);
        if (!ofs) {
            std::cerr << "❌ Error: Could not create PPM database" << std::endl;
            return;
        }
        ofs << "P6\n" << canvasSize << " " << canvasSize << "\n255\n";
        std::vector<uint8_t> blackRow(canvasSize * 3, 0);
        for (int i = 0; i < canvasSize; ++i) {
            ofs.write(reinterpret_cast<const char*>(blackRow.data()), blackRow.size());
        }
        ofs.close();
        std::cout << "✅ PPM Database Ready: " << dbPath << std::endl;
    }

    bool deleteDB(const std::string& filePath) {
        try {
            // std::filesystem::remove returns true if the file existed and was deleted
            if (std::filesystem::remove(filePath)) {
                return true;
            } else {
                return false;
            }
        } catch (const std::filesystem::filesystem_error& e) {
            std::cerr << "Filesystem Error: " << e.what() << std::endl;
            return false;
        }
    }

    // DB checking/validating functions
    size_t getFileSize(const std::string& path) {
        try {
            if (std::filesystem::exists(path) && std::filesystem::is_regular_file(path)) {
                return std::filesystem::file_size(path);
            }
        } catch (const std::filesystem::filesystem_error& e) {
            std::cerr << "❌ Filesystem Error: " << e.what() << std::endl;
        }
        return 0;
    }

    bool validateDB(const std::string& path) {
        // 4000 * 4000 * 3
        const size_t rawDataSize = 48000000; 
        size_t actual = getFileSize(path);
        if (path.find(".ppm") != std::string::npos) {
            // PPM must have the header + the data
            return actual >= (rawDataSize + 15);
        } else {
            // PNG/Raw must be at least the data size
            return actual >= rawDataSize;
        }
    }

    // Extra functions

};

#endif