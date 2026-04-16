import java.nio.file.Files;
import java.nio.file.Paths;

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