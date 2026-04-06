#ifndef SCY_KERNEL_HPP
#define SCY_KERNEL_HPP

#include <iostream>
#include <string>
#include <vector>
#include <fstream>
#include <cmath>
#include <cstdint>

class ScyKernel {
private:
    std::string password;
    std::string filePath;
    int hVal;
    const int canvasSize = 4000;

    // Deterministic FNV-1a Hash + Alphabet Salt
    int deriveIndex(const std::string& key) {
        uint32_t hash = 0x811c9dc5; // FNV offset basis
        uint32_t prime = 0x01000193; // FNV prime
        long alphaSalt = 0;

        for (char c : key) {
            // FNV-1a Math
            hash ^= (uint8_t)c;
            hash *= prime;
            // Alphabet Salt Math (A=1, B=2...)
            if (std::isalpha(c)) {
                alphaSalt += (std::tolower(c) - 'a' + 1);
            }
        }
        return std::abs((int)(hash + alphaSalt)) % 16000000;
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
        int hash = 7;
        for (char c : pwd) hash = hash * 31 + c;
        return std::abs(hash % 16000000);
    }

public:
    ScyKernel(std::string pwd, std::string path) : password(pwd), filePath(path) {
        hVal = getHVal(pwd);
    }

    void put(const std::string& key, const std::string& value) {
        int index = deriveIndex(key);
        int curD = hVal + (index * 1000);
        int x, y;
        d2xy(canvasSize, curD, x, y);

        std::fstream file(filePath, std::ios::in | std::ios::out | std::ios::binary);
        if (!file) return;

        // Header offset (approx P6 PPM)
        long offset = 15 + (y * canvasSize + x) * 3;
        file.seekp(offset);

        for (char c : value) {
            uint8_t pixel[3];
            file.read((char*)pixel, 3);
            pixel[0] ^= (uint8_t)c; // XOR Obfuscation
            file.seekp(-3, std::ios::cur);
            file.write((char*)pixel, 3);
        }
        // Write Null Terminator
        uint8_t term[3] = {0, 0, 0};
        file.write((char*)term, 3);
        file.close();
    }

    std::string get(const std::string& key) {
        int index = deriveIndex(key);
        int curD = hVal + (index * 1000);
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
};

#endif