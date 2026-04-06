import Foundation

class ScyKernel {
    private let password: String
    private let filePath: String
    private let canvasSize: Int = 4000
    private var hVal: Int = 0

    init(password: String, filePath: String) {
        self.password = password
        self.filePath = filePath
        self.hVal = getHVal(pwd: password)
    }

    private func getHVal(pwd: String) -> Int {
        var hash: Int32 = 7
        for char in pwd.unicodeScalars {
            hash = hash.addingReportingOverflow(hash.multipliedReportingOverflow(by: 30).partialValue).partialValue
            hash = hash.addingReportingOverflow(Int32(char.value)).partialValue
        }
        return abs(Int(hash % 16000000))
    }

    // Deterministic FNV-1a + Alphabet Salt for Cross-Language Parity
    private func deriveIndex(key: String) -> Int {
        var hash: UInt32 = 0x811c9dc5
        let prime: UInt32 = 0x01000193
        var alphaSalt: Int64 = 0

        let lowerKey = key.lowercased()
        let keyScalars = Array(key.unicodeScalars)
        let lowerScalars = Array(lowerKey.unicodeScalars)

        for i in 0..<keyScalars.count {
            let scalar = keyScalars[i]
            // FNV-1a Math (32-bit unsigned wrapping)
            hash ^= UInt32(scalar.value)
            hash = hash &* prime

            // Alphabet Salt (a=1, b=2...)
            if CharacterSet.letters.contains(scalar) {
                let saltVal = Int64(lowerScalars[i].value) - Int64(Unicode.Scalar("a").value) + 1
                alphaSalt += salt_val
            }
        }
        
        let combined = Int64(hash) + alphaSalt
        return Int(abs(combined) % 16000000)
    }

    private func rot(n: Int, x: Int, y: Int, rx: Int, ry: Int) -> (Int, Int) {
        var tx = x
        var ty = y
        if ry == 0 {
            if rx == 1 {
                tx = n - 1 - x
                ty = n - 1 - y
            }
            return (ty, tx)
        }
        return (tx, ty)
    }

    private func d2xy(n: Int, d: Int) -> (Int, Int) {
        var x = 0, y = 0
        var t = d
        var s = 1
        while s < n {
            let rx = 1 & (t / 2)
            let ry = 1 & (t ^ rx)
            let (nx, ny) = rot(n: s, x: x, y: y, rx: rx, ry: ry)
            x = nx + s * rx
            y = ny + s * ry
            t /= 4
            s *= 2
        }
        return (x, y)
    }

    func put(key: String, value: String) throws {
        let index = deriveIndex(key: key)
        let curD = hVal + (index * 1000)
        let (x, y) = d2xy(n: canvasSize, d: curD)

        let fileURL = URL(fileURLWithPath: filePath)
        let fileHandle = try FileHandle(forUpdating: fileURL)
        defer { fileHandle.closeFile() }

        let offset = UInt64(15 + (y * canvasSize + x) * 3)
        let data = Data(value.utf8)

        for (i, byte) in data.enumerated() {
            let pos = offset + UInt64(i * 3)
            fileHandle.seek(toFileOffset: pos)
            var pixel = fileHandle.readData(ofLength: 3)
            if pixel.isEmpty { pixel = Data([0, 0, 0]) }
            
            // XOR Obfuscation
            var pArray = [UInt8](pixel)
            pArray[0] ^= byte
            
            fileHandle.seek(toFileOffset: pos)
            fileHandle.write(Data(pArray))
        }

        // Write Null Terminator
        fileHandle.seek(toFileOffset: offset + UInt64(data.count * 3))
        fileHandle.write(Data([0, 0, 0]))
    }

    func get(key: String) throws -> String {
        let index = deriveIndex(key: key)
        let curD = hVal + (index * 1000)
        let (x, y) = d2xy(n: canvasSize, d: curD)

        let fileURL = URL(fileURLWithPath: filePath)
        let fileHandle = try FileHandle(forReadingFrom: fileURL)
        defer { fileHandle.closeFile() }

        let offset = UInt64(15 + (y * canvasSize + x) * 3)
        var resultData = Data()

        var i = 0
        while true {
            let pos = offset + UInt64(i * 3)
            fileHandle.seek(toFileOffset: pos)
            let pixel = fileHandle.readData(ofLength: 3)
            
            if pixel.isEmpty || pixel[0] == 0 { break }
            resultData.append(pixel[0])
            i += 1
        }

        return String(data: resultData, encoding: .utf8) ?? ""
    }
}