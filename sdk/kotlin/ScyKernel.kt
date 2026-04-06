package sdk.kotlin

import java.io.ByteArrayOutputStream
import java.io.File
import java.io.RandomAccessFile
import java.nio.charset.StandardCharsets
import kotlin.math.abs

class ScyKernel(private val password: String, private val filePath: String) {
    private val canvasSize = 4000
    private val hVal: Int = getHVal(password)

    private fun getHVal(pwd: String): Int {
        var hash = 7
        for (char in pwd) {
            hash = hash * 31 + char.code
        }
        return abs(hash % 16000000)
    }

    // Deterministic FNV-1a + Alphabet Salt for Cross-Language Parity
    private fun deriveIndex(key: String): Int {
        var hash = 0x811c9dc5L.toUInt()
        val prime = 0x01000193L.toUInt()
        var alphaSalt: Long = 0

        val lowerKey = key.lowercase()
        for (i in key.indices) {
            val char = key[i]
            // FNV-1a Math using Kotlin's UInt for 32-bit unsigned parity
            hash = hash xor char.code.toUInt()
            hash *= prime

            // Alphabet Salt Math (a=1, b=2...)
            if (char.isLetter()) {
                alphaSalt += (lowerKey[i].code - 'a'.code + 1).toLong()
            }
        }
        // Combine hash and salt, then constrain to 10,000 slots
        return (abs(hash.toLong() + alphaSalt) % 16000000).toInt()
    }

    private fun d2xy(n: Int, d: Int): IntArray {
        var x = 0
        var y = 0
        var t = d
        var s = 1
        while (s < n) {
            val rx = 1 and (t / 2)
            val ry = 1 and (t xor rx)
            val rotated = rot(s, x, y, rx, ry)
            x = rotated[0] + s * rx
            y = rotated[1] + s * ry
            t /= 4
            s *= 2
        }
        return intArrayOf(x, y)
    }

    private fun rot(n: Int, x: Int, y: Int, rx: Int, ry: Int): IntArray {
        var tx = x
        var ty = y
        if (ry == 0) {
            if (rx == 1) {
                tx = n - 1 - x
                ty = n - 1 - y
            }
            return intArrayOf(ty, tx)
        }
        return intArrayOf(tx, ty)
    }

    fun put(key: String, value: String) {
        val index = deriveIndex(key)
        val curD = hVal + (index * 1000)
        val coords = d2xy(canvasSize, curD)
        val (x, y) = coords

        RandomAccessFile(filePath, "rw").use { raf ->
            val offset = 15L + (y.toLong() * canvasSize + x) * 3
            val data = value.toByteArray(StandardCharsets.UTF_8)

            for (i in data.indices) {
                raf.seek(offset + (i * 3L))
                val r = raf.read().let { if (it == -1) 0 else it }
                
                raf.seek(offset + (i * 3L))
                raf.write(r xor data[i].toInt()) // XOR Obfuscation
            }
            // Null Terminator
            raf.seek(offset + (data.size * 3L))
            raf.write(byteArrayOf(0, 0, 0))
        }
    }

    fun get(key: String): String {
        val index = deriveIndex(key)
        val curD = hVal + (index * 1000)
        val coords = d2xy(canvasSize, curD)
        val (x, y) = coords

        RandomAccessFile(filePath, "r").use { raf ->
            val offset = 15L + (y.toLong() * canvasSize + x) * 3
            val bos = ByteArrayOutputStream()

            var i = 0
            while (true) {
                raf.seek(offset + (i * 3L))
                val r = raf.read()
                if (r == -1 || r == 0) break
                bos.write(r)
                i++
            }
            return bos.toString(StandardCharsets.UTF_8.name())
        }
    }
}