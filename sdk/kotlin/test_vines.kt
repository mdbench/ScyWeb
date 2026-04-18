import java.io.File
import kotlin.system.exitProcess

fun main() {
    val dir = "vines_images"
    val path = "$dir/kt_vine.ppm"
    val path2 = "$dir/kt_vine.png"
    val testKey = "User"
    val testValue = "Amanda"
    val password = "ScyWeb_Global_Secret_2026"

    // Ensure the local folder exists
    val directory = File(dir)
    if (!directory.exists()) {
        directory.mkdirs()
    }
    
    // Instantiating 'scy' with the password and the local path
    val scy = ScyKernel(password, path)

    // Creating the test DBs
    scy._createPPM_DB(path)
    scy._syncPNG(path2, "load")

    // Test both PPM and PNG DBs
    scy._putToPPM(testKey, testValue, password)
    scy._putToPNG(testKey, testValue, password)

    // sync changes and refresh
    scy._syncPNG(path2, "commit")
    scy._syncPNG(path2, "load")

    // Retrieve the results from both DBs
    val result = scy._getFromPPM(testKey, password)
    val result2 = scy._getFromPNG(testKey, password)

    // Output Comparison
    if (result == testValue && result2 == testValue) {
        val validationTest = if (scy._validateDB(path)) "Valid " else "Invalid"
        println("✅ Kotlin KV Parity: SUCCESS (Recovered: $result)")
        println("🧩 PPM is: $validationTest")
        val size = scy._getFileSize(path2)
        val sizeStr = "$size bytes"
        println("📏 Size of Image DB: $sizeStr")
        //scy.deleteDB(path)
        //scy.deleteDB(path2)
        val parityConfigs = listOf(
            "C++" to "../cpp/vines_images/cpp_vine.png",
            "Go" to "../go/scykernel/vines_images/go_vine.png",
            "Java" to "../java/vines_images/java_vine.png",
            "Node" to "../javascript/vines_images/node_vine.png",
            "Kotlin" to "../kotlin/vines_images/kt_vine.png",
            "PHP" to "../php/vines_images/php_vine.png",
            "Python" to "../python/vines_images/py_vine.png",
            "React Native" to "../react-native/vines_images/rn_vine.png",
            "Rust" to "../rust/vines_images/rust_vine.png",
            "Swift" to "../swift/vines_images/swift_vine.png"
        )
        for ((lang, lPath) in parityConfigs) {
            if (File(lPath).exists()) {
                val scyCheck = ScyKernel(password, lPath)
                if (scyCheck._syncPNG(lPath, "load")) {
                    val res = scyCheck._getFromPNG(testKey, password)
                    if (res == testValue) {
                        println("✅ Kotlin to $lang Parity: SUCCESS (Recovered: $res)")
                    } else {
                        println("❌ Kotlin to $lang Parity: FAIL")
                    }
                }
            }
        }
        exitProcess(0)
    } else {
        println("❌ Kotlin KV Parity: FAIL")
        println("Expected: $testValue, Got: [$result]")
        println("Expected: $testValue, Got: [$result2]")
        scy.deleteDB(path)
        scy.deleteDB(path2)
        exitProcess(1)
    }
}