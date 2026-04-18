import Foundation

// --- ZLIB BRIDGE (Self-Contained) ---
#if canImport(Glibc)
    import Glibc
#elseif canImport(Darwin)
    import Darwin
#endif

@_silgen_name("compress")
func c_compress(_ dest: UnsafeMutablePointer<UInt8>, _ destLen: UnsafeMutablePointer<Int>, _ source: UnsafePointer<UInt8>, _ sourceLen: Int) -> Int32

@_silgen_name("uncompress")
func c_uncompress(_ dest: UnsafeMutablePointer<UInt8>, _ destLen: UnsafeMutablePointer<Int>, _ source: UnsafePointer<UInt8>, _ sourceLen: Int) -> Int32

private func zlibCompress(_ data: Data) -> Data? {
    var destSize = Int(Double(data.count) * 1.1) + 12
    var dest = Data(count: destSize)
    let result = dest.withUnsafeMutableBytes { destBytes in
        data.withUnsafeBytes { srcBytes in
            c_compress(destBytes.bindMemory(to: UInt8.self).baseAddress!,
                       &destSize,
                       srcBytes.bindMemory(to: UInt8.self).baseAddress!,
                       data.count)
        }
    }
    guard result == 0 else { return nil }
    return dest.subdata(in: 0..<destSize)
}

private func zlibDecompress(_ data: Data, expectedSize: Int) -> Data? {
    var destSize = expectedSize
    var dest = Data(count: destSize)
    let result = dest.withUnsafeMutableBytes { destBytes in
        data.withUnsafeBytes { srcBytes in
            c_uncompress(destBytes.bindMemory(to: UInt8.self).baseAddress!,
                         &destSize,
                         srcBytes.bindMemory(to: UInt8.self).baseAddress!,
                         data.count)
        }
    }
    guard result == 0 else { return nil }
    return dest
}

public class ScyKernel {
    private var password: String
    private var filePath: String
    private var hVal: UInt32 = 0
    private let canvasSize: Int32 = 4000
    private let pixelDataSize: Int = 48000000
    private var dbBuffer: Data

    public init(pwd: String, path: String) {
        self.password = pwd
        self.filePath = path
        self.dbBuffer = Data(repeating: 0, count: pixelDataSize)
        self.hVal = getHVal(pwd: pwd)
    }

    private func getHVal(pwd: String) -> UInt32 {
        var hash: UInt32 = 7
        for byte in pwd.utf8 {
            hash = (hash &* 31) &+ UInt32(byte)
        }
        let normalized = Double(hash) / 4294967296.0
        return UInt32(floor(normalized * 16000000.0))
    }

    private func deriveIndex(key: String, password: String) -> Int32 {
        var hash: UInt32 = 0x811c9dc5
        let prime: UInt32 = 0x01000193
        var alphaSalt: UInt32 = 0
        if !password.isEmpty {
            for byte in password.utf8 {
                hash ^= UInt32(byte)
                hash = hash &* prime
            }
        }
        for byte in key.utf8 {
            hash ^= UInt32(byte)
            hash = hash &* prime
            let char = Character(UnicodeScalar(byte))
            if char.isLetter {
                let lower = char.lowercased().first!
                let val = UInt32(lower.asciiValue!) &- UInt32(Character("a").asciiValue!) &+ 1
                alphaSalt = alphaSalt &+ val
            }
        }
        let finalVal = hash &+ alphaSalt
        let normalized = Double(finalVal) / 4294967296.0
        return Int32(truncatingIfNeeded: Int64(floor(normalized * 16000000.0)))
    }

    private func d2xy(n: Int32, d: Int32, x: inout Int32, y: inout Int32) {
        var t = d
        x = 0; y = 0
        var s: Int32 = 1
        while s < n {
            let rx = 1 & (t / 2)
            let ry = 1 & (t ^ rx)
            rot(n: s, x: &x, y: &y, rx: rx, ry: ry)
            x &+= s &* rx
            y &+= s &* ry
            t /= 4
            s &*= 2
        }
    }

    private func rot(n: Int32, x: inout Int32, y: inout Int32, rx: Int32, ry: Int32) {
        if ry == 0 {
            if rx == 1 {
                x = n &- 1 &- x
                y = n &- 1 &- y
            }
            swap(&x, &y)
        }
    }

    private func cryptByte(c: UInt8, password: String, position: Int32) -> UInt8 {
        var salt: UInt32 = 0x811c9dc5
        for byte in password.utf8 {
            salt = (salt ^ UInt32(byte)) &* 16777619
        }
        let posU32 = UInt32(bitPattern: position)
        var mixed = salt ^ (posU32 &* 0xdeadbeef)
        mixed ^= (mixed >> 16)
        return c ^ UInt8(mixed & 0xFF)
    }

    private func compute_crc(buf: [UInt8]) -> UInt32 {
        var crc: UInt32 = 0xFFFFFFFF
        for byte in buf {
            crc ^= UInt32(byte)
            for _ in 0..<8 {
                if (crc & 1) != 0 {
                    crc = (crc >> 1) ^ 0xEDB88320
                } else {
                    crc >>= 1
                }
            }
        }
        return ~crc
    }

    private func write32(to out: inout Data, val: UInt32) {
        out.append(contentsOf: [
            UInt8((val >> 24) & 0xFF), UInt8((val >> 16) & 0xFF),
            UInt8((val >> 8) & 0xFF), UInt8(val & 0xFF)
        ])
    }

    // PPM sow, harvest functions
    public func putToPPM(key: String, value: String, password: String) {
        let index = deriveIndex(key: key, password: password)
        let curD = Int32(truncatingIfNeeded: Int64(hVal) &+ (Int64(index) &* 1600))
        var x: Int32 = 0; var y: Int32 = 0
        d2xy(n: canvasSize, d: curD, x: &x, y: &y)
        
        let fileURL = URL(fileURLWithPath: filePath)
        guard let file = try? FileHandle(forUpdating: fileURL) else { return }
        
        let pixelOffset = Int64(y) &* Int64(canvasSize) &+ Int64(x)
        let offset = UInt64(15 &+ (pixelOffset &* 3))
        
        do {
            try file.seek(toOffset: offset)
            let valBytes = Array(value.utf8)
            var i: Int32 = 0
            for byte in valBytes {
                if let pixelData = try file.read(upToCount: 3), pixelData.count == 3 {
                    var pixel = Array(pixelData)
                    pixel[0] = cryptByte(c: byte, password: password, position: i)
                    try file.seek(toOffset: file.offsetInFile &- 3)
                    try file.write(contentsOf: Data(pixel))
                    try file.seek(toOffset: file.offsetInFile)
                    i &+= 1
                }
            }
            try file.write(contentsOf: Data([0, 0, 0]))
            try file.close()
        } catch { return }
    }

    public func getFromPPM(key: String, password: String) -> String {
        let index = deriveIndex(key: key, password: password)
        let curD = Int32(truncatingIfNeeded: Int64(hVal) &+ (Int64(index) &* 1600))
        var x: Int32 = 0; var y: Int32 = 0
        d2xy(n: canvasSize, d: curD, x: &x, y: &y)
        
        let fileURL = URL(fileURLWithPath: filePath)
        guard let file = try? FileHandle(forReadingFrom: fileURL) else { return "" }
        
        let pixelOffset = Int64(y) &* Int64(canvasSize) &+ Int64(x)
        let offset = UInt64(15 &+ (pixelOffset &* 3))
        var decryptedBytes = [UInt8]()
        var i: Int32 = 0
        
        do {
            try file.seek(toOffset: offset)
            while true {
                guard let pixelData = try file.read(upToCount: 3), pixelData.count == 3 else { break }
                let redChannel = pixelData[0]
                if redChannel == 0 { break }
                decryptedBytes.append(cryptByte(c: redChannel, password: password, position: i))
                i &+= 1
            }
            try file.close()
        } catch { return "" }
        return String(bytes: decryptedBytes, encoding: .utf8) ?? ""
    }

    // PNG sow, harvest functions
    /**
    * Writes a value to the RAM buffer.
    * Note: You MUST call syncPNG(file, "commit") after calling this to save changes.
    */
    public func putToPNG(key: String, value: String, keyPassword: String) {
        if dbBuffer.isEmpty { dbBuffer = Data(repeating: 0, count: 48000000) }
        let index = deriveIndex(key: key, password: keyPassword)
        let curD = Int32(truncatingIfNeeded: Int64(hVal) &+ (Int64(index) &* 1600))
        var x: Int32 = 0; var y: Int32 = 0
        d2xy(n: canvasSize, d: curD, x: &x, y: &y)
        
        let valBytes = Array(value.utf8)
        for i in 0..<valBytes.count {
            let xOff = x &+ Int32(i)
            let pixelIdx = Int((Int64(y) &* Int64(canvasSize) &+ Int64(xOff)) &* 3)
            if pixelIdx >= 0 && pixelIdx &+ 2 < dbBuffer.count {
                dbBuffer[pixelIdx] = cryptByte(c: valBytes[i], password: keyPassword, position: Int32(i))
            }
        }
        let termIdx = Int((Int64(y) &* Int64(canvasSize) &+ Int64(x &+ Int32(valBytes.count))) &* 3)
        if termIdx >= 0 && termIdx &+ 2 < dbBuffer.count { dbBuffer[termIdx] = 0 }
    }

    /**
    * Retrieves a value from the RAM buffer.
    * Note: You SHOULD call syncPNG(file, "load") before this to ensure fresh data.
    */
    public func getFromPNG(key: String, keyPassword: String) -> String {
        if dbBuffer.isEmpty { return "" }
        let index = deriveIndex(key: key, password: keyPassword)
        let curD = Int32(truncatingIfNeeded: Int64(hVal) &+ (Int64(index) &* 1600))
        var x: Int32 = 0; var y: Int32 = 0
        d2xy(n: canvasSize, d: curD, x: &x, y: &y)
        
        var decryptedBytes = [UInt8]()
        var i: Int32 = 0
        while true {
            let xOff = x &+ i
            let pixelIdx = Int((Int64(y) &* Int64(canvasSize) &+ Int64(xOff)) &* 3)
            if pixelIdx < 0 || pixelIdx &+ 2 >= dbBuffer.count || dbBuffer[pixelIdx] == 0 { break }
            decryptedBytes.append(cryptByte(c: dbBuffer[pixelIdx], password: keyPassword, position: i))
            i &+= 1
        }
        return String(bytes: decryptedBytes, encoding: .utf8) ?? ""
    }

    // DB sync functions for easier DB handling
    public func syncPNG(filename: String, mode: String) -> Bool {
        let modeLower = mode.lowercased()
        let fm = FileManager.default
        if modeLower == "load" && !fm.fileExists(atPath: filename) {
            self.dbBuffer = Data(repeating: 0, count: 48000000)
            return syncPNG(filename: filename, mode: "commit")
        }
        if modeLower == "commit" {
            var filtered = Data(capacity: 48004000)
            for r in 0..<4000 {
                filtered.append(0)
                let start = r * 12000
                filtered.append(dbBuffer.subdata(in: start..<(start + 12000)))
            }
            guard let compressed = zlibCompress(filtered) else { return false }
            var outData = Data()
            outData.append(contentsOf: [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
            let ihdr: [UInt8] = [0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x0F, 0xA0, 0x00, 0x00, 0x0F, 0xA0, 0x08, 0x02, 0x00, 0x00, 0x00]
            write32(to: &outData, val: 13)
            outData.append(contentsOf: ihdr)
            write32(to: &outData, val: compute_crc(buf: ihdr))
            write32(to: &outData, val: UInt32(compressed.count))
            let idatTag: [UInt8] = [0x49, 0x44, 0x41, 0x54]
            outData.append(contentsOf: idatTag)
            outData.append(compressed)
            var crcB = Data(idatTag); crcB.append(compressed)
            write32(to: &outData, val: compute_crc(buf: Array(crcB)))
            write32(to: &outData, val: 0)
            let iend: [UInt8] = [0x49, 0x45, 0x4E, 0x44]
            outData.append(contentsOf: iend)
            write32(to: &outData, val: compute_crc(buf: iend))
            try? outData.write(to: URL(fileURLWithPath: filename))
            return true
        } else if modeLower == "load" {
            guard let fileData = try? Data(contentsOf: URL(fileURLWithPath: filename)), fileData.count > 41 else { return false }
            let cLen: UInt32 = fileData.subdata(in: 33..<37).withUnsafeBytes { $0.load(as: UInt32.self).bigEndian }
            let cData = fileData.subdata(in: 41..<Int(41 + cLen))
            guard let decompressed = zlibDecompress(cData, expectedSize: 48004000) else { return false }
            self.dbBuffer = Data(repeating: 0, count: 48000000)
            for r in 0..<4000 {
                let srcStart = (r * 12001) + 1
                let destStart = r * 12000
                dbBuffer.replaceSubrange(destStart..<(destStart + 12000), with: decompressed.subdata(in: srcStart..<(srcStart + 12000)))
            }
            return true
        }
        return false
    }

    public func syncPPM(filename: String, mode: String) -> Bool {
        let modeLower = mode.lowercased()
        let fm = FileManager.default
        if modeLower == "load" && !fm.fileExists(atPath: filename) {
            print("⚠️ PPM Database not found. Initializing new raw store...")
            self.dbBuffer = Data(repeating: 0, count: 48000000)
            return syncPPM(filename: filename, mode: "commit")
        }
        if modeLower == "commit" {
            let fileURL = URL(fileURLWithPath: filename)
            var outData = "P6\n4000 4000\n255\n".data(using: .ascii)!
            outData.append(dbBuffer)
            do {
                try outData.write(to: fileURL)
                print("✅ PPM Commit Successful: \(filename)")
                return true
            } catch {
                return false
            }
        } else if modeLower == "load" {
            let fileURL = URL(fileURLWithPath: filename)
            do {
                let fileData = try Data(contentsOf: fileURL, options: .mappedIfSafe)
                guard fileData.count >= 48000015 else { return false }
                self.dbBuffer = fileData.subdata(in: 15..<48000015)
                print("✅ PPM Load Successful: \(filename)")
                return true
            } catch {
                return false
            }
        } else {
            print("❌ Invalid Sync Mode. Use 'Commit' or 'Load'.")
            return false
        }
    }

    // Blank DB creation functions
    public func createPNG_DB(filename: String) {
        self.dbBuffer = Data(repeating: 0, count: 48000000)
        if syncPNG(filename: filename, mode: "commit") {
            print("✅ PNG initialized and loaded into buffer: \(filename)")
        } else {
            print("❌ Failed to initialize PNG database file.")
        }
    }

    public func createPPM_DB(dbPath: String) {
        let header = "P6\n4000 4000\n255\n".data(using: .ascii)!
        var outData = header
        let zeroRow = Data(repeating: 0, count: 12000)
        for _ in 0..<4000 { outData.append(zeroRow) }
        try? outData.write(to: URL(fileURLWithPath: dbPath))
    }

    // DB conversion functions
    public func convertDatabaseFormat(pngPath: String, ppmPath: String, targetFormat: String) -> Bool {
        let target = targetFormat.lowercased()
        if target == "ppm" {
            if !syncPNG(filename: pngPath, mode: "load") { return false }
            let fileURL = URL(fileURLWithPath: ppmPath)
            let headerString = "P6\n4000 4000\n255\n"
            guard var outData = headerString.data(using: .ascii) else { return false }
            outData.append(dbBuffer)
            do { try outData.write(to: fileURL); return true } catch { return false }
        } else if target == "png" {
            let fileURL = URL(fileURLWithPath: ppmPath)
            do {
                let ppmData = try Data(contentsOf: fileURL, options: .mappedIfSafe)
                guard ppmData.count >= 48000015 else { return false }
                self.dbBuffer = ppmData.subdata(in: 15..<48000015)
                if !syncPNG(filename: pngPath, mode: "commit") { return false }
                return true
            } catch { return false }
        } else { return false }
    }

    // DB Deletion and cleanup functions
    public func deleteDB(filePath: String) -> Bool {
        try? FileManager.default.removeItem(atPath: filePath)
        return true
    }

    // DB checking/validating functions
    public func validateDB(path: String) -> Bool {
        let actual = getFileSize(path: path)
        return path.lowercased().contains(".ppm") ? actual >= 48000015 : actual >= 48000000
    }

    public func getFileSize(path: String) -> UInt64 {
        let attr = try? FileManager.default.attributesOfItem(atPath: path)
        return attr?[.size] as? UInt64 ?? 0
    }

}