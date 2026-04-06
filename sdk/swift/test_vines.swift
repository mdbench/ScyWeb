import Foundation

let password = "ScyWeb_Global_Secret_2026"
let imagePath = "../../vines_images/parity_test.ppm"

let testKey = "user"
let testValue = "Amanda"

func runTest() {
    let fm = FileManager.default
    
    // Ensure PPM exists
    if !fm.fileExists(atPath: imagePath) {
        let header = "P6\n4000 4000\n255\n"
        let emptyPayload = Data(count: 4000 * 4000 * 3)
        var fileData = Data(header.utf8)
        fileData.append(emptyPayload)
        fm.createFile(atPath: imagePath, contents: fileData, attributes: nil)
    }

    let kernel = ScyKernel(password: password, filePath: imagePath)

    do {
        print("Swift: Putting key '\(testKey)'...")
        try kernel.put(key: testKey, value: testValue)

        print("Swift: Getting key '\(testKey)'...")
        let result = try kernel.get(key: testKey)

        if result == testValue {
            print("✅ Swift KV Parity: SUCCESS (Recovered: \(result))")
            exit(0)
        } else {
            print("❌ Swift KV Parity: FAIL. Expected: \(testValue), Got: \(result)")
            exit(1)
        }
    } catch {
        print("❌ Swift Error: \(error)")
        exit(1)
    }
}

runTest()