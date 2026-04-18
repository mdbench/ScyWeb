import java.io.File;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Map;
import java.util.LinkedHashMap;

public class test_vines {
    public static void main(String[] args) {
        final String dir = "vines_images";
        final String pathPPM = dir + "/java_vine.ppm";
        final String pathPNG = dir + "/java_vine.png";
        final String testKey = "User";
        final String testValue = "Amanda";
        final String password = "ScyWeb_Global_Secret_2026";

        try {
            // Ensure the local folder exists
            Files.createDirectories(Paths.get(dir));

            // Instantiate ScyKernel (Constructor: password, default path)
            ScyKernel scy = new ScyKernel(password, pathPPM);

            // Creating the test DBs
            scy.createPPM_DB(pathPPM);
            scy.syncPNG(pathPNG, "load");

            // Test both PPM and PNG DBs
            scy.putToPPM(testKey, testValue, password);
            scy.putToPNG(testKey, testValue, password);

            // sync changes and refresh
            scy.syncPNG(pathPNG, "commit");
            scy.syncPNG(pathPNG, "load");

            // Retrieve the results from both DBs
            String resultPPM = scy.getFromPPM(testKey, password);
            String resultPNG = scy.getFromPNG(testKey, password);

            // Output Comparison
            if (testValue.equals(resultPPM) && testValue.equals(resultPNG)) {
                String validationStatus = scy.validateDB(pathPPM) ? "Valid" : "Invalid";
                System.out.printf("✅ Java KV Parity: SUCCESS (Recovered: %s)%n", resultPPM);
                System.out.printf("🧩 PPM is: %s%n", validationStatus);
                long pngSize = scy.getFileSize(pathPNG);
                System.out.printf("📏 Size of Image DB: %d bytes%n", pngSize);
                //scy.deleteDB(pathPPM);
                //scy.deleteDB(pathPNG);
                Map<String, String> parityConfigs = new LinkedHashMap<>();
                parityConfigs.put("C++", "../cpp/vines_images/cpp_vine.png");
                parityConfigs.put("Go", "../go/scykernel/vines_images/go_vine.png");
                parityConfigs.put("Java", "../java/vines_images/java_vine.png");
                parityConfigs.put("Node", "../javascript/vines_images/node_vine.png");
                parityConfigs.put("Kotlin", "../kotlin/vines_images/kt_vine.png");
                parityConfigs.put("PHP", "../php/vines_images/php_vine.png");
                parityConfigs.put("Python", "../python/vines_images/py_vine.png");
                parityConfigs.put("React Native", "../react-native/vines_images/rn_vine.png");
                parityConfigs.put("Rust", "../rust/vines_images/rust_vine.png");
                parityConfigs.put("Swift", "../swift/vines_images/swift_vine.png");
                for (Map.Entry<String, String> entry : parityConfigs.entrySet()) {
                    String lang = entry.getKey();
                    String lPath = entry.getValue();
                    if (new File(lPath).exists()) {
                        ScyKernel scyCheck = new ScyKernel(password, lPath);
                        if (scyCheck.syncPNG(lPath, "load")) {
                            String res = scyCheck.getFromPNG(testKey, password);
                            if (res.equals(testValue)) {
                                System.out.println("✅ Java to " + lang + " Parity: SUCCESS (Recovered: " + res + ")");
                            } else {
                                System.out.println("❌ Java to " + lang + " Parity: FAIL");
                            }
                        }
                    }
                }
                System.exit(0);
            } else {
                System.out.println("❌ Java KV Parity: FAIL");
                System.out.printf("Expected: %s%n", testValue);
                System.out.printf("Got PPM: [%s]%n", resultPPM);
                System.out.printf("Got PNG: [%s]%n", resultPNG);
                scy.deleteDB(pathPPM);
                scy.deleteDB(pathPNG);
                System.exit(1);
            }

        } catch (Exception e) {
            System.err.println("❌ Java SDK Critical Error: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }
}