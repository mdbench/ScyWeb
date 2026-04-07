#include <iostream>
#include <fstream>
#include <string>
#include <filesystem>
#include "ScyKernel.hpp" 

namespace fs = std::filesystem;

int main() {
    const std::string dir = "vines_images";
    const std::string path = dir + "/cpp_vine.ppm";
    const std::string testKey = "User";
    const std::string testValue = "Amanda";
    const std::string password = "ScyWeb_Global_Secret_2026";

    // Ensure the local folder exists
    if (!fs::exists(dir)) {
        fs::create_directory(dir);
    }

    // Creating the bit-perfect 15-byte header + 48MB body
    std::ofstream out(path, std::ios::binary);
    if (!out) {
        std::cerr << "❌ IO Error: Could not create " << path << std::endl;
        return 1;
    }
    
    // Header Parity: printf "P6 4000 4000 255\n" | head -c 15
    out << "P6 4000 4000 25"; 
    out.seekp(15 + 48000000 - 1);
    out.put(0);
    out.close();

    // Instantiating 'scy' with the password and the local path
    ScyKernel scy(password, path);

    // Internal logic handles the +1600 offset and Hilbert mapping
    scy.put(testKey, testValue);

    // Retrieve the result
    std::string result = scy.get(testKey);

    // Output Comparison
    if (result == testValue) {
        std::cout << "✅ C++ KV Parity: SUCCESS (Recovered: " << result << ")" << std::endl;
        return 0;
    } else {
        std::cout << "❌ C++ KV Parity: FAIL" << std::endl;
        std::cout << "Expected: " << testValue << ", Got: [" << result << "]" << std::endl;
        return 1;
    }
}