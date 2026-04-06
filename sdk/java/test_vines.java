package sdk.java;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;

public class test_vines {
    public static void main(String[] args) {
        String password = "ScyWeb_Global_Secret_2026";
        String imagePath = "../../vines_images/parity_test.ppm";
        
        String testKey = "user";
        String testValue = "Amanda";

        try {
            // Ensure PPM exists for testing
            File file = new File(imagePath);
            if (!file.exists()) {
                file.getParentFile().mkdirs();
                try (FileOutputStream fos = new FileOutputStream(file)) {
                    fos.write("P6\n4000 4000\n255\n".getBytes());
                    byte[] empty = new byte[1024 * 1024]; // Write in chunks
                    for (int i = 0; i < (4000 * 4000 * 3) / empty.length; i++) {
                        fos.write(empty);
                    }
                }
            }

            ScyKernel kernel = new ScyKernel(password, imagePath);

            System.out.println("Java: Putting key '" + testKey + "'...");
            kernel.put(testKey, testValue);

            System.out.println("Java: Getting key '" + testKey + "'...");
            String result = kernel.get(testKey);

            if (testValue.equals(result)) {
                System.out.println("✅ Java KV Parity: SUCCESS (Recovered: " + result + ")");
                System.exit(0);
            } else {
                System.out.println("❌ Java KV Parity: FAIL");
                System.out.println("Expected: " + testValue + ", Got: " + result);
                System.exit(1);
            }
        } catch (Exception e) {
            System.err.println("❌ Java Error: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }
}