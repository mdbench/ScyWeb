import java.io.File
import java.io.RandomAccessFile
import java.nio.file.Files
import java.nio.file.Paths
import kotlin.system.exitProcess

fun main() {
    val testKey = "User"
    val testValue = "Amanda"
    val password = "ScyWeb_Global_Secret_2026"
    val dbDir = "vines_images"
    val dbPath = "$dbDir/kotlin_vine.ppm"

    try {
        // PHYSICAL FILE SETUP
        Files.createDirectories(Paths.get(dbDir))
        val file = File(dbPath)
        
        RandomAccessFile(file, "rw").use { raf ->
            // Exact 15-byte header parity
            val header = "P6 4000 4000 255\n".toByteArray()
            raf.write(header, 0, 15)
            
            // Allocate 48MB (4000 * 4000 * 3 + 15)
            raf.setLength(48000015L)
        }

        // INITIALIZE KERNEL
        val scy = ScyKernel(password, dbPath)

        // SOW: Put operation (Must use 1600 offset internally)
        scy.put(testKey, testValue, password)

        // HARVEST: Get operation
        val result = scy.get(testKey, password)

        if (testValue == result) {
            println("✅ Kotlin KV Parity: SUCCESS (Recovered: $result)")
            scy.deleteDB(dbPath)
            exitProcess(0)
        } else {
            println("❌ Kotlin KV Parity: FAIL")
            println("Expected: $testValue, Got: [$result]")
            scy.deleteDB(dbPath)
            exitProcess(1)
        }

    } catch (e: Exception) {
        println("❌ Kotlin SDK Error: ${e.message}")
        e.printStackTrace()
        exitProcess(1)
    }
}