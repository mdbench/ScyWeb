import Foundation

@main
struct ParityTest {
    static func main() {
        let test = ParityTest()
        test.runTest()
    }

    let dir = "vines_images"
    let path = "vines_images/swift_vine.ppm"
    let path2 = "vines_images/swift_vine.png"
    let testKey = "User"
    let testValue = "Amanda"
    let password = "ScyWeb_Global_Secret_2026"

    func runTest() {
        let fm = FileManager.default
        
        // Ensure the local folder exists
        if !fm.fileExists(atPath: dir) {
            try? fm.createDirectory(atPath: dir, withIntermediateDirectories: true, attributes: nil)
        }

        // Instantiating 'scy' with the password and the local path
        let scy = ScyKernel(pwd: password, path: path)

        // Creating the test DBs
        scy.createPPM_DB(dbPath: path)
        _ = scy.syncPNG(filename: path2, mode: "load")

        // Test both PPM and PNG DBs
        scy.putToPPM(key: testKey, value: testValue, password: password)
        scy.putToPNG(key: testKey, value: testValue, keyPassword: password)

        // Sync changes and refresh RAM buffer
        _ = scy.syncPNG(filename: path2, mode: "commit")
        _ = scy.syncPNG(filename: path2, mode: "load")

        // Retrieve the results from both DBs
        let result = scy.getFromPPM(key: testKey, password: password)
        let result2 = scy.getFromPNG(key: testKey, keyPassword: password)

        // Output Comparison
        if result == testValue && result2 == testValue {
            let validationTest = scy.validateDB(path: path) ? "Valid" : "Invalid"
            print("✅ Swift KV Parity: SUCCESS (Recovered: \(result))")
            print("🧩 PPM is: \(validationTest)")
            
            let size = scy.getFileSize(path: path2)
            print("📏 Size of Image DB: \(size) bytes")

            // --- START CROSS-LANGUAGE PARITY CHECK ---
            
            let parityChecks = [
                ("C++", "../cpp/vines_images/cpp_vine.png"),
                ("Go", "../go/scykernel/vines_images/go_vine.png"),
                ("Java", "../java/vines_images/java_vine.png"),
                ("Node", "../javascript/vines_images/node_vine.png"),
                ("Kotlin", "../kotlin/vines_images/kt_vine.png"),
                ("PHP", "../php/vines_images/php_vine.png"),
                ("Python", "../python/vines_images/py_vine.png"),
                ("React Native", "../react-native/vines_images/rn_vine.png"),
                ("Rust", "../rust/vines_images/rust_vine.png"),
                ("Swift", "../swift/vines_images/swift_vine.png")
            ]

            for (language, vPath) in parityChecks {
                let scyParity = ScyKernel(pwd: password, path: vPath)
                if scyParity.syncPNG(filename: vPath, mode: "load") {
                    let resParity = scyParity.getFromPNG(key: testKey, keyPassword: password)
                    if resParity == testValue {
                        print("✅ Swift to \(language) Parity: SUCCESS (Recovered: \(resParity))")
                    } else {
                        print("❌ Swift to \(language) Parity: FAIL")
                    }
                }
            }
            // --- END CROSS-LANGUAGE PARITY CHECK ---
            exit(0)
            
        } else {
            print("❌ Swift KV Parity: FAIL")
            print("Expected: \(testValue), Got (PPM): [\(result)]")
            print("Expected: \(testValue), Got (PNG): [\(result2)]")
            _ = scy.deleteDB(filePath: path)
            _ = scy.deleteDB(filePath: path2)
            exit(1)
        }
    }
}