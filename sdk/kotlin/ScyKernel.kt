import java.io.RandomAccessFile
import java.io.File
import kotlin.math.*
import java.util.Locale
import java.nio.file.Files
import java.nio.file.Paths

class ScyKernel(private val password: String, private val filePath: String) {
    private val canvasSize: Int = 4000
    private var hVal: Long = 0
    private var dbBuffer: ByteArray? = null

    init {
        this.hVal = getHVal(password).toLong()
        this.dbBuffer = null
    }

    private fun getHVal(pwd: String): Int {
        var hash: Int;
        hash = 7
        for (c in pwd) {
            hash = hash * 31 + c.code
        }
        var unsignedHash: Long;
        unsignedHash = hash.toLong() and 0xFFFFFFFFL
        var normalized: Double;
        normalized = unsignedHash.toDouble() / 4294967296.0
        var result: Int;
        result = floor(normalized * 16000000.0).toInt()
        return result
    }

    private fun _deriveIndex(key: String, password: String): Int {
        var hash = 0x811c9dc5L
        val prime = 0x01000193L
        var alphaSalt = 0L
        for (c in password) {
            hash = hash xor (c.code.toLong() and 0xFFL)
            hash = (hash * prime) and 0xFFFFFFFFL
        }
        for (c in key) {
            hash = hash xor (c.code.toLong() and 0xFFL)
            hash = (hash * prime) and 0xFFFFFFFFL
            if (c.isLetter()) {
                alphaSalt += (c.lowercaseChar().code - 'a'.code + 1).toLong()
            }
        }
        val finalVal = (hash + alphaSalt) and 0xFFFFFFFFL
        val normalized = (finalVal.toDouble() / 4294967296.0) * 16000000.0
        return kotlin.math.floor(normalized).toInt()
    }

    private fun _rot(n: Int, x: Int, y: Int, rx: Int, ry: Int): Pair<Int, Int> {
        var tx = x
        var ty = y
        if (ry == 0) {
            if (rx == 1) {
                tx = n - 1 - x
                ty = n - 1 - y
            }
            return Pair(ty, tx)
        }
        return Pair(tx, ty)
    }

    private fun _d2xy(n: Int, d: Long): Pair<Int, Int> {
        var x = 0
        var y = 0
        var t = d
        var s = 1
        while (s < n) {
            val rx = (1L and (t / 2)).toInt()
            val ry = (1L and (t xor rx.toLong())).toInt()
            val (nx, ny) = _rot(s, x, y, rx, ry)
            x = nx + s * rx
            y = ny + s * ry
            t /= 4
            s *= 2
        }
        return Pair(x, y)
    }

    /**
     * A bit-perfect, zero-byte overhead encryption layer.
     * XORs the character based on the password's hash and the character's position.
     */
    private fun _cryptByte(c: Char, password: String, position: Int): Char {
        var salt: UInt = 0x811c9dc5u 
        for (pc in password) {
            salt = (salt xor pc.code.toUInt()) * 16777619u 
        }
        var mixed: UInt = salt xor (position.toUInt() * 0xdeadbeefu)
        mixed = mixed xor (mixed shr 16)
        val keyByte = (mixed and 0xFFu).toByte()
        return (c.code xor (keyByte.toInt() and 0xFF)).toChar()
    }

    // Lightweight CRC-32 for PNG Chunk Compliance
    private fun _compute_crc(buf: ByteArray, len: Int): UInt {
        var crc: UInt = 0xFFFFFFFFu
        for (i in 0 until len) {
            crc = crc xor (buf[i].toUInt() and 0xFFu)
            for (j in 0 until 8) {
                // Implementing -(crc & 1) logic via mask
                val mask = if ((crc and 1u) == 1u) 0xEDB88320u else 0u
                crc = (crc shr 1) xor mask
            }
        }
        return crc.inv()
    }

    private fun _write32(out: java.io.OutputStream, val32: UInt) {
        val b = byteArrayOf(
            (val32 shr 24).toByte(),
            (val32 shr 16).toByte(),
            (val32 shr 8).toByte(),
            val32.toByte()
        )
        out.write(b, 0, 4)
    }

    // PPM sow, harvest functions
    /**
    * Writes a value directly to the PPM file on disk.
    */
    fun _putToPPM(key: String, value: String, password: String) {
        val index = _deriveIndex(key, password)
        val curD = hVal + (index * 1600)
        val (x, y) = _d2xy(canvasSize, curD)

        try {
            val file = java.io.RandomAccessFile(filePath, "rw")
            val offset = 15L + (y.toLong() * canvasSize + x) * 3L
            file.seek(offset)
            var i = 0 
            for (c in value) {
                val pixel = ByteArray(3)
                val bytesRead = file.read(pixel)
                if (bytesRead < 3) break
                val secureChar = _cryptByte(c, password, i)
                pixel[0] = secureChar.code.toByte()
                file.seek(file.filePointer - 3)
                file.write(pixel)
                i++
            }
            val term = byteArrayOf(0, 0, 0)
            file.write(term)
            file.close()
        } catch (e: Exception) {}
    }

    fun _getFromPPM(key: String, password: String): String {
        val index = _deriveIndex(key, password)
        val curD = hVal + (index * 1600)
        val (x, y) = _d2xy(canvasSize, curD)
        try {
            val file = java.io.RandomAccessFile(filePath, "r")
            val offset = 15L + (y.toLong() * canvasSize + x) * 3L
            file.seek(offset)
            var result = ""
            var i = 0
            while (true) {
                val pixel = ByteArray(3)
                val bytesRead = file.read(pixel)
                if (bytesRead < 3 || pixel[0].toInt() == 0) break
                val scrambled = (pixel[0].toInt() and 0xFF).toChar()
                result += _cryptByte(scrambled, password, i)
                i++
            }
            file.close()
            return result
        } catch (e: Exception) {
            return ""
        }
    }

    // PNG sow, harvest functions
    /**
    * Writes a value to the RAM buffer.
    * Note: You MUST call syncPNG(file, "commit") after calling this to save changes.
    */
    fun _putToPNG(key: String, value: String, keyPassword: String) {
        if (dbBuffer == null || dbBuffer!!.isEmpty()) {
            dbBuffer = ByteArray(48000000)
        }
        val index = _deriveIndex(key, keyPassword)
        val curD = hVal + (index * 1600)
        val (x, y) = _d2xy(canvasSize, curD)
        for (i in value.indices) {
            val pixelIdx = ((y * canvasSize) + (x + i)) * 3
            if ((pixelIdx + 2) < dbBuffer!!.size) {
                val secureChar = _cryptByte(value[i], keyPassword, i)
                dbBuffer!![pixelIdx] = secureChar.code.toByte()
            }
        }
        val termIdx = ((y * canvasSize) + (x + value.length)) * 3
        if ((termIdx + 2) < dbBuffer!!.size) {
            dbBuffer!![termIdx] = 0.toByte()
        }
    }

    /**
    * Retrieves a value from the RAM buffer.
    * Note: You SHOULD call syncPNG(file, "load") before this to ensure fresh data.
    */
    fun _getFromPNG(key: String, keyPassword: String): String {
        if (dbBuffer == null || dbBuffer!!.isEmpty()) return "" 
        val index = _deriveIndex(key, keyPassword)
        val curD = hVal + (index * 1600)
        val (x, y) = _d2xy(canvasSize, curD)
        var result = ""
        var i = 0
        while (true) {
            val pixelIdx = ((y * canvasSize) + (x + i)) * 3
            if ((pixelIdx + 2) >= dbBuffer!!.size || dbBuffer!![pixelIdx].toInt() == 0) {
                break
            }
            val scrambled = (dbBuffer!![pixelIdx].toInt() and 0xFF).toChar()
            result += _cryptByte(scrambled, keyPassword, i)
            i++
        }
        return result
    }

    // DB sync functions for easier DB handling
    fun _syncPNG(filename: String, modeIn: String): Boolean {
        val mode = modeIn.lowercase()
        if (mode == "load" && !java.io.File(filename).exists()) {
            println("⚠️ Database not found. Initializing new compressed store...")
            dbBuffer = ByteArray(48000000)
            return _syncPNG(filename, "commit")
        }
        if (mode == "commit") {
            val filtered = ByteArray(48004000)
            for (r in 0 until 4000) {
                filtered[r * 12001] = 0
                dbBuffer?.copyInto(filtered, r * 12001 + 1, r * 12000, (r + 1) * 12000)
            }
            val deflater = java.util.zip.Deflater(java.util.zip.Deflater.BEST_COMPRESSION)
            deflater.setInput(filtered)
            deflater.finish()
            val compressedOutput = java.io.ByteArrayOutputStream()
            val compBuf = ByteArray(1024)
            while (!deflater.finished()) {
                val count = deflater.deflate(compBuf)
                compressedOutput.write(compBuf, 0, count)
            }
            val compressed = compressedOutput.toByteArray()
            try {
                val out = java.io.FileOutputStream(filename)
                val sig = byteArrayOf(0x89.toByte(), 0x50.toByte(), 0x4E.toByte(), 0x47.toByte(), 0x0D.toByte(), 0x0A.toByte(), 0x1A.toByte(), 0x0A.toByte())
                out.write(sig)
                val ihdr = byteArrayOf('I'.code.toByte(), 'H'.code.toByte(), 'D'.code.toByte(), 'R'.code.toByte(), 0, 0, 0x0F.toByte(), 0xA0.toByte(), 0, 0, 0x0F.toByte(), 0xA0.toByte(), 8, 2, 0, 0, 0)
                _write32(out, 13u)
                out.write(ihdr)
                _write32(out, _compute_crc(ihdr, 17))
                _write32(out, compressed.size.toUInt())
                val idatTag = "IDAT".toByteArray()
                out.write(idatTag)
                out.write(compressed)
                val crcB = java.io.ByteArrayOutputStream()
                crcB.write(idatTag)
                crcB.write(compressed)
                _write32(out, _compute_crc(crcB.toByteArray(), crcB.size()))
                _write32(out, 0u)
                val iendTag = "IEND".toByteArray()
                out.write(iendTag)
                _write32(out, _compute_crc(iendTag, 4))
                out.close()
                println("✅ PNG Commit Successful: $filename")
                return true
            } catch (e: Exception) {
                return false
            }
        } else if (mode == "load") {
            try {
                val file = java.io.File(filename)
                val fis = java.io.FileInputStream(file)
                val fullData = fis.readBytes()
                fis.close()
                val bis = java.io.ByteArrayInputStream(fullData)
                bis.skip(33)
                val lBuf = ByteArray(4)
                bis.read(lBuf)
                val cLen = ((lBuf[0].toUInt() and 0xFFu) shl 24) or 
                           ((lBuf[1].toUInt() and 0xFFu) shl 16) or 
                           ((lBuf[2].toUInt() and 0xFFu) shl 8) or 
                           (lBuf[3].toUInt() and 0xFFu)
                bis.skip(4)
                val cData = ByteArray(cLen.toInt())
                bis.read(cData)
                val inflater = java.util.zip.Inflater()
                inflater.setInput(cData)
                val decomp = ByteArray(48004000)
                inflater.inflate(decomp)
                inflater.end()
                dbBuffer = ByteArray(48000000)
                for (r in 0 until 4000) {
                    decomp.copyInto(dbBuffer!!, r * 12000, r * 12001 + 1, (r + 1) * 12001)
                }
                //println("✅ PNG Load Successful: $filename")
                return true
            } catch (e: Exception) {
                return false
            }
        } else {
            System.err.println("❌ Invalid Sync Mode. Use 'Commit' or 'Load'.")
            return false
        }
    }

    fun _syncPPM(filename: String, modeIn: String): Boolean {
        val mode = modeIn.lowercase()
        if (mode == "load" && !java.io.File(filename).exists()) {
            println("⚠️ PPM Database not found. Initializing new raw store...")
            dbBuffer = ByteArray(48000000)
            return _syncPPM(filename, "commit")
        }
        if (mode == "commit") {
            try {
                val out = java.io.FileOutputStream(filename)
                out.write("P6\n4000 4000\n255\n".toByteArray())
                dbBuffer?.let { out.write(it) }
                out.close()
                println("✅ PPM Commit Successful: $filename")
                return true
            } catch (e: Exception) {
                return false
            }
        } else if (mode == "load") {
            try {
                val file = java.io.File(filename)
                val fis = java.io.FileInputStream(file)
                fis.skip(15)
                dbBuffer = ByteArray(48000000)
                fis.read(dbBuffer)
                fis.close()
                println("✅ PPM Load Successful: $filename")
                return true
            } catch (e: Exception) {
                return false
            }
        } else {
            System.err.println("❌ Invalid Sync Mode. Use 'Commit' or 'Load'.")
            return false
        }
    }

    // Blank DB creation functions
    fun _createPNG_DB(filename: String) {
        dbBuffer = ByteArray(48000000)
        if (_syncPNG(filename, "commit")) {
            println("✅ PNG initialized and loaded into buffer: $filename")
        } else {
            System.err.println("❌ Failed to initialize PNG database file.")
        }
    }

    fun _createPPM_DB(dbPath: String) {
        try {
            val fos = java.io.FileOutputStream(dbPath)
            // Write the P6 Header (Standard 4000x4000 8-bit RGB)
            val header = "P6\n$canvasSize $canvasSize\n255\n"
            fos.write(header.toByteArray())
            val zeroRow = ByteArray(canvasSize * 3)
            for (i in 0 until canvasSize) {
                fos.write(zeroRow)
            }
            fos.close()
            println("✅ PPM Database Ready (Isolated from RAM): $dbPath")
        } catch (e: Exception) {
            System.err.println("❌ Error: Could not create PPM database")
            return
        }
    }

    // DB conversion functions
    fun _convertDatabaseFormat(pngPath: String, ppmPath: String, targetFormat: String): Boolean {
        // Standardize the flag to lowercase to handle "PNG", "png", "Ppm", etc.
        val format = targetFormat.lowercase()
        if (format == "ppm") { 
            // SOURCE: PNG -> TARGET: PPM (Decompress and Expand)
            if (!_syncPNG(pngPath, "load")) {
                System.err.println("❌ Failed to load PNG database.")
                return false
            }
            try {
                val ppmFile = java.io.File(ppmPath)
                val fos = java.io.FileOutputStream(ppmFile)
                // Write P6 PPM Header (Standard 4000x4000 8-bit)
                fos.write("P6\n4000 4000\n255\n".toByteArray())
                // Dump the raw 48MB buffer into the file
                dbBuffer?.let { fos.write(it) }
                fos.close()
                println("✅ Converted PNG to PPM (48MB Raw Volume)")
                return true
            } catch (e: Exception) {
                return false
            }
        } else if (format == "png") { 
            // SOURCE: PPM -> TARGET: PNG (Pack and Compress)
            try {
                val ppmFile = java.io.File(ppmPath)
                if (!ppmFile.exists()) return false
                val fis = java.io.FileInputStream(ppmFile)
                // Skip the header (Assuming "P6\n4000 4000\n255\n" is 15 bytes)
                fis.skip(15)
                // Read the raw 48MB into our RAM buffer
                val rawDataSize = 48000000
                dbBuffer = ByteArray(rawDataSize)
                fis.read(dbBuffer, 0, rawDataSize)
                fis.close()
                // Use syncPNG to compress and save as a PNG
                if (!_syncPNG(pngPath, "commit")) {
                    System.err.println("❌ Failed to compress and save PNG database.")
                    return false
                }
                println("✅ Converted PPM to PNG")
                return true
            } catch (e: Exception) {
                return false
            }
        } else {
            System.err.println("❌ Invalid target format. Use 'PNG' or 'PPM'.")
            return false
        }
    }

    // DB Deletion and cleanup functions
    fun deleteDB(dbPath: String): Boolean {
        return Files.deleteIfExists(Paths.get(dbPath))
    }

    // DB checking/validating functions
    fun _getFileSize(path: String): Long {
        try {
            val file = java.io.File(path)
            if (file.exists() && file.isFile) {
                return file.length()
            }
        } catch (e: Exception) {
            System.err.println("❌ Filesystem Error: ${e.message}")
        }
        return 0
    }

    fun _validateDB(path: String): Boolean {
        // 4000 * 4000 * 3
        val rawDataSize: Long = 48000000
        val actual = _getFileSize(path)
        if (path.contains(".ppm")) {
            // PPM must have the header + the data
            return actual >= (rawDataSize + 15)
        } else {
            // PNG/Raw must be at least the data size
            return actual >= rawDataSize
        }
    }

}