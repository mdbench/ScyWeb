import java.io.File;
import java.io.RandomAccessFile;
import java.nio.file.Files;
import java.nio.file.Paths;

public class test_vines {
    public static void main(String[] args) {
        String testKey = "User";
        String testValue = "Amanda";
        String password = "ScyWeb_Global_Secret_2026";
        String dbDir = "vines_images";
        String dbPath = dbDir + "/java_vine.ppm";

        try {
            // PHYSICAL FILE SETUP
            Files.createDirectories(Paths.get(dbDir));
            File file = new File(dbPath);
            
            try (RandomAccessFile raf = new RandomAccessFile(file, "rw")) {
                // Write exact 15-byte header parity
                byte[] header = "P6 4000 4000 255\n".getBytes();
                raf.write(header, 0, 15);
                
                // Allocate 48MB (Total: 48,000,015 bytes)
                raf.setLength(48000015);
            }

            // INITIALIZE KERNEL
            // Ensuring the constructor matches: (password, path)
            ScyKernel scy = new ScyKernel(password, dbPath);

            // SOW: Put operation (Must use 1600 offset internally)
            scy.put(testKey, testValue);

            // HARVEST: Get operation
            String result = scy.get(testKey);

            // CLEANUP & VALIDATION
            if (file.exists()) {
                file.delete();
            }

            if (testValue.equals(result)) {
                System.out.printf("✅ Java KV Parity: SUCCESS (Recovered: %s)%n", result);
                System.exit(0);
            } else {
                System.out.println("❌ Java KV Parity: FAIL");
                System.out.printf("Expected: %s, Got: [%s]%n", testValue, result);
                System.exit(1);
            }

        } catch (Exception e) {
            System.err.println("❌ Java SDK Error: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }
}