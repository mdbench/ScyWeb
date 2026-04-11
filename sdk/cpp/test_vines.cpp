#include <iostream>
#include <fstream>
#include <string>
#include <filesystem>
#include "ScyKernel.hpp" 

namespace fs = std::filesystem;

int main() {
    const std::string dir = "vines_images";
    const std::string path = dir + "/cpp_vine.ppm";
    const std::string path2 = dir + "/cpp_vine.png";
    const std::string testKey = "User";
    const std::string testValue = "Amanda";
    const std::string password = "ScyWeb_Global_Secret_2026";

    // Ensure the local folder exists
    if (!fs::exists(dir)) {
        fs::create_directory(dir);
    }
    
    // Instantiating 'scy' with the password and the local path
    ScyKernel scy(password, path);

    // Creating the test DBs
    scy.createPPM_DB(path);
    scy.syncDatabase(path2, 1);

    // Test both PPM and PNG DBs
    scy.putToPPM(testKey, testValue, password);
    scy.putToPNG(testKey, testValue, password);

    // sync changes and refresh
    scy.syncDatabase(path2, 0);
    scy.syncDatabase(path2, 1);

    // Retrieve the results from both DBs
    std::string result = scy.getFromPPM(testKey, password);
    std::string result2 = scy.getFromPNG(testKey, password);

    // Output Comparison
    if (result == testValue && result2 == testValue) {
        std::string validationTest = scy.validateDB(path) ? "Valid " : "Invalid";
        std::cout << "✅ C++ KV Parity: SUCCESS (Recovered: " << result << ")" << std::endl;
        std::cout << "🧩 PPM is: " << validationTest << std::endl;
        size_t size = scy.getFileSize(path2);
        std::string sizeStr = std::to_string(size) + " bytes";
        std::cout << "📐 Size of Image DB: " << sizeStr << std::endl;
        //scy.deleteDB(path);
        //scy.deleteDB(path2);
        return 0;
    } else {
        std::cout << "❌ C++ KV Parity: FAIL" << std::endl;
        std::cout << "Expected: " << testValue << ", Got: [" << result << "]" << std::endl;
        std::cout << "Expected: " << testValue << ", Got: [" << result2 << "]" << std::endl;
        scy.deleteDB(path);
        scy.deleteDB(path2);
        return 1;
    }
}