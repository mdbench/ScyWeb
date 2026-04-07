import java.io.RandomAccessFile
import java.io.File
import kotlin.math.*
import java.util.Locale

class ScyKernel(private val password: String, private val filePath: String) {
    private val canvasSize: Int = 4000
    private var hVal: Long = 0

    init {
        this.hVal = getHVal(password).toLong()
    }

    private fun getHVal(pwd: String): Int {
        var hash: UInt = 7u
        for (char in pwd) {
            // Fix: Use .toInt() instead of .code
            hash = hash * 31u + char.toInt().toUInt()
        }
        return ((hash.toDouble() / 4294967296.0) * 16000000.0).toInt()
    }

    private fun deriveIndex(key: String): Long {
        var hash: UInt = 0x811c9dc5u
        val prime: UInt = 0x01000193u
        var alphaSalt: Long = 0
        
        val lowerKey = key.lowercase(Locale.getDefault())
        val aInt = 'a'.toInt()

        for (i in key.indices) {
            val char = key[i]
            hash = hash xor char.toInt().toUInt()
            hash *= prime

            if (char.isLetter()) {
                // Fix: Use .toInt() instead of .code
                alphaSalt += (lowerKey[i].toInt() - aInt + 1).toLong()
            }
        }
        val finalVal = (hash.toLong() + alphaSalt).toUInt()
        return ((finalVal.toDouble() / 4294967296.0) * 16000000.0).toLong()
    }

    private fun rot(n: Int, x: Int, y: Int, rx: Int, ry: Int): Pair<Int, Int> {
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

    private fun d2xy(n: Int, d: Long): Pair<Int, Int> {
        var x = 0
        var y = 0
        var t = d
        var s = 1
        while (s < n) {
            val rx = (1L and (t / 2)).toInt()
            val ry = (1L and (t xor rx.toLong())).toInt()
            val (nx, ny) = rot(s, x, y, rx, ry)
            x = nx + s * rx
            y = ny + s * ry
            t /= 4
            s *= 2
        }
        return Pair(x, y)
    }

    fun put(key: String, value: String) {
        val index = deriveIndex(key)
        val curD = hVal + (index * 1600)
        val (x, y) = d2xy(canvasSize, curD)

        RandomAccessFile(File(filePath), "rw").use { raf ->
            val offset = 15L + (y.toLong() * canvasSize + x) * 3
            val bytes = value.toByteArray(Charsets.UTF_8)

            for (i in bytes.indices) {
                val pos = offset + (i * 3)
                raf.seek(pos)
                val pixel = ByteArray(3)
                val read = raf.read(pixel)
                
                // XOR Obfuscation
                pixel[0] = (pixel[0].toInt() xor bytes[i].toInt()).toByte()
                
                raf.seek(pos)
                raf.write(pixel)
            }
            // Null terminator
            raf.seek(offset + (bytes.size * 3))
            raf.write(byteArrayOf(0, 0, 0))
        }
    }

    fun get(key: String): String {
        val index = deriveIndex(key)
        val curD = hVal + (index * 1600)
        val (x, y) = d2xy(canvasSize, curD)

        RandomAccessFile(File(filePath), "r").use { raf ->
            val offset = 15L + (y.toLong() * canvasSize + x) * 3
            val result = mutableListOf<Byte>()
            var i = 0
            while (true) {
                raf.seek(offset + (i * 3))
                val pixel = ByteArray(3)
                if (raf.read(pixel) <= 0 || pixel[0] == 0.toByte()) break
                result.add(pixel[0])
                i++
            }
            return String(result.toByteArray(), Charsets.UTF_8)
        }
    }
}