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
        int i = 0; // Positional tracker for cryptByte
        for (char c : value) {
            uint8_t pixel[3];
            // Read 3 bytes (the current pixel)
            file.read((char*)pixel, 3);
            // Apply ScyKernel stream cipher before storage
            char secureChar = cryptByte(c, password, i);
            // Direct assignment to Red channel to match putToPNG logic
            pixel[0] = (uint8_t)secureChar; 
            // Move back 3 bytes to overwrite the SAME pixel we just read
            file.seekp(-3, std::ios::cur);
            file.write((char*)pixel, 3);
            // Ensure the read pointer is also updated for the next iteration if needed
            file.seekg(file.tellp());
            i++;
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
        int i = 0; 
        while (true) {
            uint8_t pixel[3];
            file.read((char*)pixel, 3);
            if (pixel[0] == 0 || file.eof()) break; 
            char scrambled = (char)pixel[0];
            result += cryptByte(scrambled, password, i);
            i++;
        }
        file.close();
        return result;
    }

    // PNG sow, harvest functions
    /**
    * Writes a value to the RAM buffer.
    * Note: You MUST call syncPNG(file, "commit") after calling this to save changes.
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
    * Note: You SHOULD call syncPNG(file, "load") before this to ensure fresh data.
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

    // DB sync functions for easier DB handling
    bool syncPNG(const std::string& filename, std::string mode) {
        std::transform(mode.begin(), mode.end(), mode.begin(), ::tolower);
        // Check if we are in LOAD MODE but the file is missing
        if (mode == "load" && !std::filesystem::exists(filename)) {
            std::cout << "⚠️ Database not found. Initializing new compressed store..." << std::endl;
            // Zero out the buffer and force a COMMIT to create the valid PNG structure
            dbBuffer.assign(48000000, 0);
            return syncPNG(filename, "commit"); 
        }
        if (mode == "commit") { // COMMIT MODE (RAM -> Disk)
            std::vector<uint8_t> filtered;
            filtered.reserve(48004000);
            for (int r = 0; r < 4000; r++) {
                filtered.push_back(0); // Row Filter (Type 0: None)
                filtered.insert(filtered.end(), 
                                dbBuffer.begin() + (r * 12000), 
                                dbBuffer.begin() + ((r + 1) * 12000));
            }
            uLongf cSize = compressBound(filtered.size());
            std::vector<uint8_t> compressed(cSize);
            if (compress(compressed.data(), &cSize, filtered.data(), filtered.size()) != Z_OK) return false;
            compressed.resize(cSize);
            std::ofstream out(filename, std::ios::binary);
            const uint8_t sig[] = {0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A};
            out.write((char*)sig, 8);
            uint8_t ihdr[] = {'I','H','D','R', 0,0,0x0F,0xA0, 0,0,0x0F,0xA0, 8, 2, 0, 0, 0};
            write32(out, 13); 
            out.write((char*)ihdr, 17); 
            write32(out, compute_crc(ihdr, 17));
            write32(out, compressed.size());
            out.write("IDAT", 4); 
            out.write((char*)compressed.data(), compressed.size());
            std::vector<uint8_t> crcB = {'I','D','A','T'};
            crcB.insert(crcB.end(), compressed.begin(), compressed.end());
            write32(out, compute_crc(crcB.data(), crcB.size()));
            write32(out, 0); 
            out.write("IEND", 4); 
            write32(out, compute_crc((uint8_t*)"IEND", 4));
            std::cout << "✅ PNG Commit Successful: " << filename << std::endl;
            return true;
        } else if (mode == "load") { // LOAD MODE (Disk -> RAM)
            std::ifstream file(filename, std::ios::binary);
            if (!file) return false;
            file.seekg(33);
            uint32_t cLen;
            char lBuf[4]; 
            file.read(lBuf, 4);
            cLen = (uint8_t(lBuf[0]) << 24) | (uint8_t(lBuf[1]) << 16) | 
                (uint8_t(lBuf[2]) << 8)  | uint8_t(lBuf[3]);
            file.seekg(4, std::ios::cur);
            std::vector<uint8_t> cData(cLen);
            file.read((char*)cData.data(), cLen);
            uLongf uSize = 48004000;
            std::vector<uint8_t> decomp(uSize);
            if (uncompress(decomp.data(), &uSize, cData.data(), cLen) != Z_OK) return false;
            dbBuffer.assign(48000000, 0);
            for (int r = 0; r < 4000; r++) {
                std::copy(decomp.begin() + (r * 12001) + 1, 
                        decomp.begin() + (r * 12001) + 12001, 
                        dbBuffer.begin() + (r * 12000));
            }
            std::cout << "✅ PNG Load Successful: " << filename << std::endl;
            return true;
        } else {
            std::cerr << "❌ Invalid Sync Mode. Use 'Commit' or 'Load'." << std::endl;
            return false;
        }
    }

    bool syncPPM(const std::string& filename, std::string mode) {
        std::transform(mode.begin(), mode.end(), mode.begin(), ::tolower);
        // Check if we are in LOAD MODE but the file is missing
        if (mode == "load" && !std::filesystem::exists(filename)) {
            std::cout << "⚠️ PPM Database not found. Initializing new raw store..." << std::endl;
            dbBuffer.assign(48000000, 0);
            return syncPPM(filename, "commit");
        }
        if (mode == "commit") { // COMMIT MODE (RAM -> Disk)
            std::ofstream out(filename, std::ios::binary);
            if (!out) return false;
            out << "P6\n4000 4000\n255\n";
            out.write(reinterpret_cast<const char*>(dbBuffer.data()), dbBuffer.size());
            out.close();
            std::cout << "✅ PPM Commit Successful: " << filename << std::endl;
            return true;
        } else if (mode == "load") { // LOAD MODE (Disk -> RAM)
            std::ifstream file(filename, std::ios::binary);
            if (!file) return false;
            file.seekg(15);
            dbBuffer.resize(48000000);
            file.read(reinterpret_cast<char*>(dbBuffer.data()), 48000000);
            file.close();
            std::cout << "✅ PPM Load Successful: " << filename << std::endl;
            return true;
        } else {
            std::cerr << "❌ Invalid Sync Mode. Use 'Commit' or 'Load'." << std::endl;
            return false;
        }
    }

    // Blank DB creation functions
    void createPNG_DB(const std::string& filename) {
        dbBuffer.assign(48000000, 0);
        if (syncPNG(filename, "commit")) {
            std::cout << "✅ PNG initialized and loaded into buffer: " << filename << std::endl;
        } else {
            std::cerr << "❌ Failed to initialize PNG database file." << std::endl;
        }
    }

    void createPPM_DB(const std::string& dbPath) {
        std::ofstream ofs(dbPath, std::ios::binary);
        if (!ofs) {
            std::cerr << "❌ Error: Could not create PPM database" << std::endl;
            return;
        }
        // Write the P6 Header (Standard 4000x4000 8-bit RGB)
        ofs << "P6\n" << canvasSize << " " << canvasSize << "\n255\n";
        std::vector<uint8_t> zeroRow(canvasSize * 3, 0);
        for (int i = 0; i < canvasSize; ++i) {
            ofs.write(reinterpret_cast<const char*>(zeroRow.data()), zeroRow.size());
        }
        ofs.close();
        std::cout << "✅ PPM Database Ready (Isolated from RAM): " << dbPath << std::endl;
    }

    // DB conversion functions
    bool convertDatabaseFormat(const std::string& pngPath, const std::string& ppmPath, std::string targetFormat) {
        // Standardize the flag to lowercase to handle "PNG", "png", "Ppm", etc.
        std::transform(targetFormat.begin(), targetFormat.end(), targetFormat.begin(), ::tolower);
        if (targetFormat == "ppm") { 
            // SOURCE: PNG -> TARGET: PPM (Decompress and Expand)
            if (!syncPNG(pngPath, "load")) {
                std::cerr << "❌ Failed to load PNG database." << std::endl;
                return false;
            }
            std::ofstream ppm(ppmPath, std::ios::binary);
            if (!ppm) return false;
            // Write P6 PPM Header (Standard 4000x4000 8-bit)
            ppm << "P6\n4000 4000\n255\n";
            // Dump the raw 48MB buffer into the file
            ppm.write((char*)dbBuffer.data(), dbBuffer.size());
            ppm.close();
            std::cout << "✅ Converted PNG to PPM (48MB Raw Volume)" << std::endl;
            return true;
        } else if (targetFormat == "png") { 
            // SOURCE: PPM -> TARGET: PNG (Pack and Compress)
            std::ifstream ppm(ppmPath, std::ios::binary);
            if (!ppm) return false;
            // Skip the header (Assuming "P6\n4000 4000\n255\n" is 15 bytes)
            ppm.seekg(15);
            // Read the raw 48MB into our RAM buffer
            dbBuffer.resize(48000000);
            ppm.read((char*)dbBuffer.data(), 48000000);
            ppm.close();
            // Use syncPNG to compress and save as a PNG
            if (!syncPNG(pngPath, "commit")) {
                std::cerr << "❌ Failed to compress and save PNG database." << std::endl;
                return false;
            }
            std::cout << "✅ Converted PPM to PNG" << std::endl;
            return true;
        } else {
            std::cerr << "❌ Invalid target format. Use 'PNG' or 'PPM'." << std::endl;
            return false;
        }
    }

    // DB Deletion and cleanup functions
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