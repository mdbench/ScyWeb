package sdk.kotlin

import java.io.File
import java.io.FileOutputStream
import kotlin.system.exitProcess

fun main() {
    val password = "ScyWeb_Global_Secret_2026"
    val imagePath = "../../vines_images/parity_test.ppm"
    
    val testKey = "user"
    val testValue = "Amanda"

    try {
        val file = File(imagePath)
        if (!file.exists()) {
            file.parentFile.mkdirs()
            FileOutputStream(file).use { fos ->
                fos.write("P6\n4000 4000\n255\n".toByteArray())
                val empty = ByteArray(1024 * 1024)
                repeat((4000 * 4000 * 3) / empty.size) {
                    fos.write(empty)
                }
            }
        }

        val kernel = ScyKernel(password, imagePath)

        println("Kotlin: Putting key '$testKey'...")
        kernel.put(testKey, testValue)

        println("Kotlin: Getting key '$testKey'...")
        val result = kernel.get(testKey)

        if (testValue == result) {
            println("✅ Kotlin KV Parity: SUCCESS (Recovered: $result)")
            exitProcess(0)
        } else {
            println("❌ Kotlin KV Parity: FAIL")
            println("Expected: $testValue, Got: $result")
            exitProcess(1)
        }
    } catch (e: Exception) {
        System.err.println("❌ Kotlin Error: ${e.message}")
        e.printStackTrace()
        exitProcess(1)
    }
}