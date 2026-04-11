import Foundation

public class ScyKernel {
    private let password: String
    private let filePath: String
    private let canvasSize: Int = 4000
    private var hVal: Int64 = 0

    public init(password: String, filePath: String) {
        self.password = password
        self.filePath = filePath
        self.hVal = Int64(getHVal(pwd: password))
    }

    private func getHVal(pwd: String) -> Int {
        var hash: UInt32 = 7
        for char in pwd.unicodeScalars {
            hash = (hash &* 31) &+ UInt32(char.value)
        }
        return Int((Double(hash) / 4294967296.0) * 16000000.0)
    }

    private func deriveIndex(key: String, password: String) -> Int64 {
        var hash: UInt32 = 0x811c9dc5
        let prime: UInt32 = 0x01000193
        var alphaSalt: Int64 = 0
        let aValue = Int64(Unicode.Scalar("a").value)

        for b in password.utf8 {
            hash ^= UInt32(b)
            hash = hash &* prime
        }

        for scalar in key.lowercased().unicodeScalars {
            hash ^= UInt32(scalar.value)
            hash = hash &* prime
            if CharacterSet.letters.contains(scalar) {
                alphaSalt += Int64(scalar.value) - aValue + 1
            }
        }
        let finalVal = UInt32(truncatingIfNeeded: Int64(hash) + alphaSalt)
        return Int64((Double(finalVal) / 4294967296.0) * 16000000.0)
    }

    private func rot(n: Int, x: Int, y: Int, rx: Int, ry: Int) -> (Int, Int) {
        if ry == 0 {
            if rx == 1 { return (n - 1 - y, n - 1 - x) }
            return (y, x)
        }
        return (x, y)
    }

    private func d2xy(n: Int, d: Int64) -> (Int, Int) {
        var x = 0, y = 0, t = d, s = 1
        while s < n {
            let rx = Int(1 & (t / 2))
            let ry = Int(1 & (t ^ Int64(rx)))
            let (nx, ny) = rot(n: s, x: x, y: y, rx: rx, ry: ry)
            x = nx + s * rx
            y = ny + s * ry
            t /= 4; s *= 2
        }
        return (x, y)
    }

    public func put(key: String, value: String, password: String) throws {
        let index = deriveIndex(key: key, password: password)
        let (x, y) = d2xy(n: canvasSize, d: hVal + (index * 1600))
        let handle = try FileHandle(forUpdating: URL(fileURLWithPath: filePath))
        defer { try? handle.close() }

        let offset = 15 + (Int64(y) * Int64(canvasSize) + Int64(x)) * 3
        let data = Array(value.utf8)

        for (i, byte) in data.enumerated() {
            let pos = UInt64(offset + Int64(i * 3))
            try handle.seek(toOffset: pos)
            var pixel = (try? handle.read(upToCount: 3)) ?? Data([0, 0, 0])
            if pixel.count < 3 { pixel = Data([0,0,0]) }
            var pArray = [UInt8](pixel)
            pArray[0] ^= byte
            try handle.seek(toOffset: pos)
            try handle.write(contentsOf: Data(pArray))
        }
        try handle.seek(toOffset: UInt64(offset + Int64(data.count * 3)))
        try handle.write(contentsOf: Data([0, 0, 0]))
    }

    public func get(key: String, password: String) throws -> String {
        let index = deriveIndex(key: key, password: password)
        let (x, y) = d2xy(n: canvasSize, d: hVal + (index * 1600))
        let handle = try FileHandle(forReadingFrom: URL(fileURLWithPath: filePath))
        defer { try? handle.close() }

        let offset = 15 + (Int64(y) * Int64(canvasSize) + Int64(x)) * 3
        var res = Data()
        var i: Int64 = 0
        while true {
            try handle.seek(toOffset: UInt64(offset + (i * 3)))
            guard let p = try handle.read(upToCount: 3), !p.isEmpty, p[0] != 0 else { break }
            res.append(p[0]); i += 1
        }
        return String(data: res, encoding: .utf8) ?? ""
    }

    public func deleteDB(path: String) throws -> Bool {
        let fm = FileManager.default
        if fm.fileExists(atPath: path) {
            try fm.removeItem(atPath: path)
            return true
        }
        return false
    }
    
}