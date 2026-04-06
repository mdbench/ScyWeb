#include "ScyKernel.hpp"
#include <iostream>
#include <string>
#include <vector>

int main() {
    std::string password = "ScyWeb_Global_Secret_2026";
    std::string imagePath = "../../vines_images/parity_test.ppm";
    
    // The "Amanda" Integration Strategy
    std::string testKey = "user";
    std::string testValue = "Amanda";

    try {
        // Initialize a dummy PPM if it doesn't exist (for CI)
        std::ifstream f(imagePath);
        if(!f.good()) {
            std::ofstream out(imagePath, std::ios::binary);
            out << "P6\n4000 4000\n255\n";
            std::vector<char> empty(4000 * 4000 * 3, 0);
            out.write(empty.data(), empty.size());
            out.close();
        }
        f.close();

        ScyKernel kernel(password, imagePath);

        std::cout << "C++: Putting key '" << testKey << "'..." << std::endl;
        kernel.put(testKey, testValue);

        std::cout << "C++: Getting key '" << testKey << "'..." << std::endl;
        std::string result = kernel.get(testKey);

        if (result == testValue) {
            std::cout << "✅ C++ KV Parity: SUCCESS (Recovered: " << result << ")" << std::endl;
            return 0;
        } else {
            std::cout << "❌ C++ KV Parity: FAIL" << std::endl;
            std::cout << "Expected: " << testValue << ", Got: " << result << std::endl;
            return 1;
        }
    } catch (const std::exception& e) {
        std::cerr << "❌ C++ Exception: " << e.what() << std::endl;
        return 1;
    }
}