#include <iostream>
#include <fstream>
#include <string>
#include <filesystem>
#include <vector>
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
    scy.syncPNG(path2, "load");

    // Test both PPM and PNG DBs
    scy.putToPPM(testKey, testValue, password);
    scy.putToPNG(testKey, testValue, password);

    // sync changes and refresh
    scy.syncPNG(path2, "commit");
    scy.syncPNG(path2, "load");

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
        struct ParityConfig { std::string lang; std::string path; };
        std::vector<ParityConfig> configs = {
            {"C++", "../cpp/vines_images/cpp_vine.png"},
            {"Go", "../go/scykernel/vines_images/go_vine.png"},
            {"Java", "../java/vines_images/java_vine.png"},
            {"Node", "../javascript/vines_images/node_vine.png"},
            {"Kotlin", "../kotlin/vines_images/kt_vine.png"},
            {"PHP", "../php/vines_images/php_vine.png"},
            {"Python", "../python/vines_images/py_vine.png"},
            {"React Native", "../react-native/vines_images/rn_vine.png"},
            {"Rust", "../rust/vines_images/rust_vine.png"},
            {"Swift", "../swift/vines_images/swift_vine.png"}
        };
        for (const auto& cfg : configs) {
            if (std::filesystem::exists(cfg.path)) {
                ScyKernel scyCheck(password, cfg.path);
                if (scyCheck.syncPNG(cfg.path, "load")) {
                    std::string res = scyCheck.getFromPNG(testKey, password);
                    if (res == testValue) {
                        std::cout << "✅ C++ to " << cfg.lang << " Parity: SUCCESS (Recovered: " << res << ")" << std::endl;
                    } else {
                        std::cout << "❌ C++ to " << cfg.lang << " Parity: FAIL" << std::endl;
                    }
                }
            }
        }
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