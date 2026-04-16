import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.io.IOException;
import java.io.FileOutputStream;
import java.util.Arrays;
import java.nio.ByteBuffer;
import java.util.zip.*;

public class ScyKernel {
    private String password;
    private String filePath;
    private int hVal;
    private final int canvasSize = 4000;
    private byte[] dbBuffer;

    public ScyKernel(String pwd, String path) {
        this.password = pwd;
        this.filePath = path;
        this.hVal = getHVal(pwd);
        this.dbBuffer = new byte[canvasSize * canvasSize * 3];
    }

    private int getHVal(String pwd) {
        int hash = 7;
        for (int i = 0; i < pwd.length(); i++) {
            hash = hash * 31 + pwd.charAt(i);
        }
        return (int) (((double) (hash & 0xFFFFFFFFL) / 4294967296.0) * 16000000);
    }

    // Deterministic FNV-1a Hash + Alphabet Salt for Cross-Language Parity
    private int deriveIndex(String key, String password) {
        long hash = 0x811c9dc5L & 0xffffffffL; // FNV offset basis (uint32)
        long prime = 0x01000193L;              // FNV prime
        long alphaSalt = 0;
        for (byte b : password.getBytes()) {
            hash ^= (b & 0xFF); // Ensure unsigned byte treatment
            hash = (hash * prime) & 0xFFFFFFFFL; // Mask to 32-bit
        }
        String lowerKey = key.toLowerCase();
        for (int i = 0; i < key.length(); i++) {
            char c = key.charAt(i);
            // FNV-1a Math (keep it 32-bit unsigned logic)
            hash ^= (key.charAt(i) & 0xff);
            hash = (hash * prime) & 0xffffffffL;
            // Alphabet Salt Math (A=1, B=2...)
            if (Character.isLetter(c)) {
                alphaSalt += (lowerKey.charAt(i) - 'a' + 1);
            }
        }
        long finalHash = (hash + alphaSalt) & 0xFFFFFFFFL;
        double normalized = ((double) finalHash / 4294967296.0) * 16000000.0;
        return (int) Math.floor(normalized);
    }

    private void d2xy(int n, int d, int[] coords) {
        int x = 0, y = 0, t = d;
        for (int s = 1; s < n; s *= 2) {
            int rx = 1 & (t / 2);
            int ry = 1 & (t ^ rx);
            rot(s, x, y, rx, ry, coords);
            x = coords[0];
            y = coords[1];
            x += s * rx;
            y += s * ry;
            t /= 4;
        }
        coords[0] = x;
        coords[1] = y;
    }

    private void rot(int n, int x, int y, int rx, int ry, int[] coords) {
        if (ry == 0) {
            if (rx == 1) {
                x = n - 1 - x;
                y = n - 1 - y;
            }
            int temp = x;
            x = y;
            y = temp;
        }
        coords[0] = x;
        coords[1] = y;
    }

    public byte cryptByte(byte data, String password, int position) {
        if (password == null || password.isEmpty()) return data;
        int charIndex = position % password.length();
        int salt = password.charAt(charIndex) ^ position;
        int result = (data & 0xFF) ^ (salt & 0xFF);
        return (byte) result;
    }

    public int compute_crc(byte[] buf, int len) {
        int crc = 0xFFFFFFFF;
        for (int i = 0; i < len; i++) {
            crc ^= (buf[i] & 0xFF);
            for (int j = 0; j < 8; j++) {
                if ((crc & 1) != 0) {
                    crc = (crc >>> 1) ^ 0xEDB88320;
                } else {
                    crc = (crc >>> 1);
                }
            }
        }
        return ~crc;
    }

    public void write32(OutputStream out, int val) throws IOException {
        byte[] b = new byte[] {
            (byte)(val >>> 24),
            (byte)(val >>> 16),
            (byte)(val >>> 8),
            (byte)val
        };
        out.write(b);
    }

    private void writePNGChunk(OutputStream out, String type, byte[] data) throws IOException {
        write32(out, data.length);
        byte[] typeBytes = type.getBytes();
        byte[] crcTarget = new byte[typeBytes.length + data.length];
        System.arraycopy(typeBytes, 0, crcTarget, 0, typeBytes.length);
        System.arraycopy(data, 0, crcTarget, typeBytes.length, data.length);
        out.write(crcTarget);
        write32(out, compute_crc(crcTarget, crcTarget.length));
    }

    public void putToPPM(String key, String value, String password) {
        int index = deriveIndex(key, password);
        int curD = hVal + (index * 1600);
        // Coordinates derived from fractal mapping
        int[] coords = new int[2];
        d2xy(canvasSize, curD, coords);
        int x = coords[0];
        int y = coords[1];
        // RandomAccessFile allows simultaneous read/write with seeking
        try (RandomAccessFile file = new RandomAccessFile(filePath, "rw")) {
            // Header offset (approx P6 PPM)
            long offset = 15 + ((long) y * canvasSize + x) * 3;
            file.seek(offset);
            int i = 0; // Positional tracker for cryptByte
            for (char c : value.toCharArray()) {
                byte[] pixel = new byte[3];
                // Read 3 bytes (the current pixel)
                file.read(pixel);
                // Apply stream cipher before storage
                byte secureChar = cryptByte((byte) c, password, i);
                // Direct assignment to Red channel to match putToPNG logic
                pixel[0] = secureChar;
                // Move back 3 bytes to overwrite the SAME pixel we just read
                file.seek(file.getFilePointer() - 3);
                file.write(pixel);
                i++;
            }
            // Write Null Terminator (0 in Red channel)
            byte[] term = {0, 0, 0};
            file.write(term);
        } catch (IOException e) {
            System.err.println("❌ PPM Write Error: " + e.getMessage());
        }
    }

    public String getFromPPM(String key, String password) {
        int index = deriveIndex(key, password);
        int curD = hVal + (index * 1600);
        int[] coords = new int[2];
        d2xy(canvasSize, curD, coords);
        int x = coords[0];
        int y = coords[1];
        try (RandomAccessFile file = new RandomAccessFile(filePath, "r")) {
            long offset = 15 + ((long) y * canvasSize + x) * 3;
            file.seek(offset);
            StringBuilder result = new StringBuilder();
            int i = 0;
            while (true) {
                byte[] pixel = new byte[3];
                int bytesRead = file.read(pixel);
                // Break on Null Terminator (Red == 0) or EOF
                if (bytesRead == -1 || pixel[0] == 0) break;
                byte scrambled = pixel[0];
                result.append((char) (cryptByte(scrambled, password, i) & 0xFF));
                i++;
            }
            return result.toString();
        } catch (IOException e) {
            return "";
        }
    }

    // PNG sow, harvest functions
    /**
     * Writes a value to the RAM buffer.
     * Note: You MUST call syncPNG(file, "commit") after calling this to save changes.
     */
    public void putToPNG(String key, String value, String keyPassword) {
        // Safety check: ensure buffer is initialized
        if (dbBuffer == null || dbBuffer.length == 0) dbBuffer = new byte[48000000];
        int index = deriveIndex(key, keyPassword);
        int curD = hVal + (index * 1600);
        int[] coords = new int[2];
        d2xy(canvasSize, curD, coords);
        int x = coords[0];
        int y = coords[1];
        // Linear pixel walk in RAM
        for (int i = 0; i < value.length(); i++) {
            // Note: Casting long to handle potential overflow in indexing, though 48MB is safe for int
            int pixelIdx = ((y * canvasSize) + (x + i)) * 3;
            if (pixelIdx + 2 < dbBuffer.length) {
                byte secureChar = cryptByte((byte) value.charAt(i), keyPassword, i);
                // XOR into Red Channel (Bit-perfect data preservation)
                dbBuffer[pixelIdx] = secureChar;
            }
        }
        // Write Null Terminator (0 in Red channel marks the end)
        int termIdx = ((y * canvasSize) + (x + value.length())) * 3;
        if (termIdx + 2 < dbBuffer.length) {
            dbBuffer[termIdx] = 0;
        }
    }

    /**
     * Retrieves a value from the RAM buffer.
     * Note: You SHOULD call syncPNG(file, "load") before this to ensure fresh data.
     */
    public String getFromPNG(String key, String keyPassword) {
        if (dbBuffer == null || dbBuffer.length == 0) return "";
        int index = deriveIndex(key, keyPassword);
        int curD = hVal + (index * 1600);
        int[] coords = new int[2];
        d2xy(canvasSize, curD, coords);
        int x = coords[0];
        int y = coords[1];
        StringBuilder result = new StringBuilder();
        int i = 0;
        while (true) {
            int pixelIdx = ((y * canvasSize) + (x + i)) * 3;
            // Bounds check + Null Terminator check (Red == 0)
            if (pixelIdx + 2 >= dbBuffer.length || dbBuffer[pixelIdx] == 0) {
                break;
            }
            byte scrambled = dbBuffer[pixelIdx];
            result.append((char) (cryptByte(scrambled, keyPassword, i) & 0xFF));
            i++;
        }
        return result.toString();
    }

    // DB sync functions for easier DB handling
    public boolean syncPNG(String filename, String mode) {
        String lowerMode = mode.toLowerCase();
        if (lowerMode.equals("load") && !Files.exists(Paths.get(filename))) {
            System.out.println("⚠️ Database not found. Initializing new compressed store...");
            Arrays.fill(dbBuffer, (byte) 0);
            return syncPNG(filename, "commit");
        }
        if (lowerMode.equals("commit")) {
            try (FileOutputStream fos = new FileOutputStream(filename)) {
                // Prepare Filtered Data
                byte[] filtered = new byte[48004000];
                for (int r = 0; r < 4000; r++) {
                    filtered[r * 12001] = 0; 
                    System.arraycopy(dbBuffer, r * 12000, filtered, (r * 12001) + 1, 12000);
                }
                // Compress
                Deflater deflater = new Deflater();
                deflater.setInput(filtered);
                deflater.finish();
                byte[] compressed = new byte[48004000];
                int compressedSize = deflater.deflate(compressed);
                deflater.end();
                // Write PNG Structure
                fos.write(new byte[]{(byte)0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A});
                byte[] ihdrBody = new byte[]{
                    0,0,(byte)0x0F,(byte)0xA0, // 4000
                    0,0,(byte)0x0F,(byte)0xA0, // 4000
                    8, 2, 0, 0, 0
                };
                writePNGChunk(fos, "IHDR", ihdrBody);
                writePNGChunk(fos, "IDAT", Arrays.copyOf(compressed, compressedSize));
                writePNGChunk(fos, "IEND", new byte[0]);
                System.out.println("✅ PNG Commit Successful: " + filename);
                return true;
            } catch (IOException e) {
                return false;
            }
        } else if (lowerMode.equals("load")) {
            try (DataInputStream dis = new DataInputStream(new FileInputStream(filename))) {
                dis.skipBytes(33); // Skip Sig and IHDR
                int cLen = dis.readInt();
                dis.skipBytes(4); // Skip 'IDAT'
                byte[] cData = new byte[cLen];
                dis.readFully(cData);
                Inflater inflater = new Inflater();
                inflater.setInput(cData);
                byte[] decomp = new byte[48004000];
                inflater.inflate(decomp);
                inflater.end();
                for (int r = 0; r < 4000; r++) {
                    System.arraycopy(decomp, (r * 12001) + 1, dbBuffer, r * 12000, 12000);
                }
                System.out.println("✅ PNG Load Successful: " + filename);
                return true;
            } catch (IOException | DataFormatException e) {
                return false;
            }
        }
        return false;
    }

    public boolean syncPPM(String filename, String mode) {
        String lowerMode = mode.toLowerCase();
        if (lowerMode.equals("load") && !Files.exists(Paths.get(filename))) {
            System.out.println("⚠️ PPM Database not found. Initializing new raw store...");
            Arrays.fill(dbBuffer, (byte) 0);
            return syncPPM(filename, "commit");
        }
        if (lowerMode.equals("commit")) {
            try (FileOutputStream fos = new FileOutputStream(filename)) {
                fos.write(("P6\n4000 4000\n255\n").getBytes());
                fos.write(dbBuffer);
                System.out.println("✅ PPM Commit Successful: " + filename);
                return true;
            } catch (IOException e) {
                return false;
            }
        } else if (lowerMode.equals("load")) {
            try (FileInputStream fis = new FileInputStream(filename)) {
                fis.skip(15);
                fis.read(dbBuffer);
                System.out.println("✅ PPM Load Successful: " + filename);
                return true;
            } catch (IOException e) {
                return false;
            }
        }
        return false;
    }

    // Blank DB creation functions
    public void createPNG_DB(String filename) {
        Arrays.fill(dbBuffer, (byte) 0);
        if (syncPNG(filename, "commit")) {
            System.out.println("✅ PNG initialized and loaded into buffer: " + filename);
        } else {
            System.err.println("❌ Failed to initialize PNG database file.");
        }
    }

    public void createPPM_DB(String dbPath) {
        try (FileOutputStream ofs = new FileOutputStream(dbPath)) {
            // Write the P6 Header (Standard 4000x4000 8-bit RGB)
            String header = "P6\n" + canvasSize + " " + canvasSize + "\n255\n";
            ofs.write(header.getBytes());
            byte[] zeroRow = new byte[canvasSize * 3];
            Arrays.fill(zeroRow, (byte) 0);
            for (int i = 0; i < canvasSize; i++) {
                ofs.write(zeroRow);
            }
            System.out.println("✅ PPM Database Ready (Isolated from RAM): " + dbPath);
        } catch (IOException e) {
            System.err.println("❌ Error: Could not create PPM database - " + e.getMessage());
        }
    }

    // DB conversion functions
    public boolean convertDatabaseFormat(String pngPath, String ppmPath, String targetFormat) {
        // Standardize the flag to lowercase to handle "PNG", "png", "Ppm", etc.
        String lowerTarget = targetFormat.toLowerCase();
        if (lowerTarget.equals("ppm")) {
            // SOURCE: PNG -> TARGET: PPM (Decompress and Expand)
            if (!syncPNG(pngPath, "load")) {
                System.err.println("❌ Failed to load PNG database.");
                return false;
            }
            try (FileOutputStream ppm = new FileOutputStream(ppmPath)) {
                // Write P6 PPM Header (Standard 4000x4000 8-bit)
                String header = "P6\n4000 4000\n255\n";
                ppm.write(header.getBytes());
                // Dump the raw 48MB buffer into the file
                ppm.write(dbBuffer);
                System.out.println("✅ Converted PNG to PPM (48MB Raw Volume)");
                return true;
            } catch (IOException e) {
                System.err.println("❌ IO Error during PPM export: " + e.getMessage());
                return false;
            }
        } else if (lowerTarget.equals("png")) {
            // SOURCE: PPM -> TARGET: PNG (Pack and Compress)
            try (FileInputStream ppm = new FileInputStream(ppmPath)) {
                // Skip the header (Assuming standard 15-byte offset)
                long skipped = ppm.skip(15);
                if (skipped < 15) {
                    System.err.println("❌ Invalid PPM header encountered.");
                    return false;
                }
                // Read the raw 48MB into our RAM buffer
                int totalRead = 0;
                while (totalRead < 48000000) {
                    int read = ppm.read(dbBuffer, totalRead, 48000000 - totalRead);
                    if (read == -1) break; // EOF
                    totalRead += read;
                }
                // Use syncPNG to compress the buffer and save as a PNG
                if (!syncPNG(pngPath, "commit")) {
                    System.err.println("❌ Failed to compress and save PNG database.");
                    return false;
                }
                System.out.println("✅ Converted PPM to PNG");
                return true;
            } catch (IOException e) {
                System.err.println("❌ IO Error during PNG import: " + e.getMessage());
                return false;
            }
        } else {
            System.err.println("❌ Invalid target format. Use 'PNG' or 'PPM'.");
            return false;
        }
    }

    // DB Deletion and cleanup functions
    public boolean deleteDB(String dbPath) throws IOException {
        Path path = Paths.get(dbPath);
        try {
            // Files.deleteIfExists returns true if the file was there and deleted,
            // and false if the file didn't exist.
            return Files.deleteIfExists(path);
        } catch (IOException e) {
            // Log the error or rethrow depending on your SDK's error policy
            System.err.println("Failed to delete database: " + e.getMessage());
            throw e; 
        }
    }

    // DB checking/validating functions
    public long getFileSize(String pathStr) {
        try {
            Path path = Paths.get(pathStr);
            if (Files.exists(path) && Files.isRegularFile(path)) {
                return Files.size(path);
            }
        } catch (IOException e) {
            System.err.println("❌ Filesystem Error: " + e.getMessage());
        }
        return 0L;
    }

    public boolean validateDB(String path) {
        // 4000 * 4000 * 3
        final long rawDataSize = 48000000L; 
        long actual = getFileSize(path);
        if (path.toLowerCase().endsWith(".ppm")) {
            // PPM must have the header + the data
            return actual >= (rawDataSize + 15);
        } else {
            // PNG/Raw must be at least the data size
            return actual >= rawDataSize;
        }
    }

    // Extra functions

}