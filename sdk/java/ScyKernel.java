package sdk.java;

import java.io.*;
import java.nio.charset.StandardCharsets;

public class ScyKernel {
    private String password;
    private String filePath;
    private int hVal;
    private final int canvasSize = 4000;

    public ScyKernel(String pwd, String path) {
        this.password = pwd;
        this.filePath = path;
        this.hVal = getHVal(pwd);
    }

    private int getHVal(String pwd) {
        int hash = 7;
        for (int i = 0; i < pwd.length(); i++) {
            hash = hash * 31 + pwd.charAt(i);
        }
        return Math.abs(hash % 16000000);
    }

    // Deterministic FNV-1a Hash + Alphabet Salt for Cross-Language Parity
    private int deriveIndex(String key) {
        long hash = 0x811c9dc5L & 0xffffffffL; // FNV offset basis (uint32)
        long prime = 0x01000193L;              // FNV prime
        long alphaSalt = 0;

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
        return (int) (Math.abs(hash + alphaSalt) % 16000000);
    }

    private int[] d2xy(int n, int d) {
        int x = 0, y = 0, t = d;
        for (int s = 1; s < n; s *= 2) {
            int rx = 1 & (t / 2);
            int ry = 1 & (t ^ rx);
            int[] rotated = rot(s, x, y, rx, ry);
            x = rotated[0] + s * rx;
            y = rotated[1] + s * ry;
            t /= 4;
        }
        return new int[]{x, y};
    }

    private int[] rot(int n, int x, int y, int rx, int ry) {
        if (ry == 0) {
            if (rx == 1) {
                x = n - 1 - x;
                y = n - 1 - y;
            }
            return new int[]{y, x};
        }
        return new int[]{x, y};
    }

    public void put(String key, String value) throws IOException {
        int index = deriveIndex(key);
        int curD = hVal + (index * 1000);
        int[] coords = d2xy(canvasSize, curD);
        int x = coords[0], y = coords[1];

        try (RandomAccessFile raf = new RandomAccessFile(filePath, "rw")) {
            // P6 Header offset (~15 bytes)
            long offset = 15 + (long) (y * canvasSize + x) * 3;
            byte[] data = value.getBytes(StandardCharsets.UTF_8);

            for (int i = 0; i < data.length; i++) {
                raf.seek(offset + (i * 3L));
                int r = raf.read();
                if (r == -1) r = 0;
                
                raf.seek(offset + (i * 3L));
                raf.write(r ^ data[i]); // XOR Obfuscation
            }
            // Write Null Terminator
            raf.seek(offset + (data.length * 3L));
            raf.write(new byte[]{0, 0, 0});
        }
    }

    public String get(String key) throws IOException {
        int index = deriveIndex(key);
        int curD = hVal + (index * 1000);
        int[] coords = d2xy(canvasSize, curD);
        int x = coords[0], y = coords[1];

        try (RandomAccessFile raf = new RandomAccessFile(filePath, "r")) {
            long offset = 15 + (long) (y * canvasSize + x) * 3;
            ByteArrayOutputStream bos = new ByteArrayOutputStream();

            for (int i = 0; ; i++) {
                raf.seek(offset + (i * 3L));
                int r = raf.read();
                if (r == -1 || r == 0) break;
                bos.write(r);
            }
            return bos.toString(StandardCharsets.UTF_8);
        }
    }
}