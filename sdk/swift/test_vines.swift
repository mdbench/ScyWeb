import Foundation

@main
struct ParityTest {
    static func main() {
        let test = ParityTest()
        test.runTest()
    }

    let password = "ScyWeb_Global_Secret_2026"
    let imagePath = "vines_images/parity_test.ppm"
    let testKey = "user"
    let testValue = "Amanda"

    func runTest() {
        let fm = FileManager.default
        
        let dir = (imagePath as NSString).deletingLastPathComponent
        if !dir.isEmpty && !fm.fileExists(atPath: dir) {
            try? fm.createDirectory(atPath: dir, withIntermediateDirectories: true)
        }

        if !fm.fileExists(atPath: imagePath) {
            //print("Allocating 48MB soil file...")
            let header = "P6 4000 4000 255\n".prefix(15)
            var fileData = Data(header.utf8)
            fileData.count = 48_000_015 
            let success = fm.createFile(atPath: imagePath, contents: fileData, attributes: nil)
            if !success { exit(1) }
        }

        let kernel = ScyKernel(password: password, filePath: imagePath)

        do {
            //print("Swift: Putting key '\(testKey)'...")
            try kernel.put(key: testKey, value: testValue)

            //print("Swift: Getting key '\(testKey)'...")
            let result = try kernel.get(key: testKey)

            if fm.fileExists(atPath: imagePath) {
                //print("Cleaning up...")
                try fm.removeItem(atPath: imagePath)
            }

            if result == testValue {
                print("✅ Swift KV Parity: SUCCESS (Recovered: \(result))")
                exit(0)
            } else {
                print("❌ Swift KV Parity: FAIL. Got: [\(result)]")
                exit(1)
            }
        } catch {
            print("❌ Error: \(error)")
            try? fm.removeItem(atPath: imagePath)
            exit(1)
        }
    }
}