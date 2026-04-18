package scykernel

import (
	"io"
	"fmt"
	"os"
	"strings"
	"math"
	"unicode"
	"encoding/binary"
	"bytes"
	"compress/zlib"
)

type ScyKernel struct {
	password   string
	filePath   string
	hVal       int
	canvasSize int
	dbBuffer   []byte
}

func NewScyKernel(pwd, path string) *ScyKernel {
	kernel := &ScyKernel{
		password:   pwd,
		filePath:   path,
		canvasSize: 4000,
	}
	kernel.hVal = kernel.getHVal(pwd)
	return kernel
}

func (k *ScyKernel) getHVal(pwd string) int {
	var hash uint32
	hash = 7
	for _, c := range pwd {
		hash = (hash * 31) + uint32(c)
	}
	var normalized float64
	normalized = float64(hash) / 4294967296.0
	var result int
	result = int(math.Floor(normalized * 16000000.0))
	return result
}

// Manual FNV-1a + Alphabet Salt for Cross-Language Parity
func (k *ScyKernel) deriveIndex(key string, password string) int {
	var hash uint32
	hash = 0x811c9dc5
	var prime uint32
	prime = 0x01000193
	var alphaSalt uint32
	alphaSalt = 0
	if password != "" {
		for _, c := range password {
			hash ^= uint32(c & 0xFF)
			hash *= prime
		}
	}
	for _, c := range key {
		hash ^= uint32(c & 0xFF)
		hash *= prime
		if unicode.IsLetter(c) {
			var saltVal uint32
			saltVal = uint32(unicode.ToLower(c) - 'a' + 1)
			alphaSalt += saltVal
		}
	}
	//fmt.Printf("DEBUG [Go]: Final Hash: %d\n", hash)
    //fmt.Printf("DEBUG [Go]: Alpha Salt: %d\n", alphaSalt)
	var finalVal uint32
	finalVal = hash + alphaSalt
	var normalized float64
	normalized = float64(finalVal) / 4294967296.0
	var result int
	result = int(math.Floor(normalized * 16000000.0))
	return result
}

func (k *ScyKernel) rot(n int, x *int, y *int, rx int, ry int) {
	if ry == 0 {
		if rx == 1 {
			var limit int
			limit = n - 1
			*x = limit - *x
			*y = limit - *y
		}
		*x, *y = *y, *x
	}
}

func (k *ScyKernel) D2xy(n int, d int, x *int, y *int) {
	var rx int
	var ry int
	var s int
	var t uint32
	t = uint32(d)
	*x = 0
	*y = 0
	for s = 1; s < n; s *= 2 {
		rx = int(1 & (t / 2))
		ry = int(1 & (t ^ uint32(rx)))
		k.rot(s, x, y, rx, ry)
		*x = *x + (s * rx)
		*y = *y + (s * ry)
		t = t / 4
	}
}

/**
 * A bit-perfect, zero-byte overhead encryption layer.
 * XORs the character based on the password's hash and the character's position.
 */
 func CryptByte(c byte, password string, position int) byte {
    var salt uint32
    salt = 0x811c9dc5
    var prime uint32
    prime = 16777619
    for i := 0; i < len(password); i++ {
        var charByte uint32
        charByte = uint32(password[i] & 0xFF)
        salt = (salt ^ charByte)
        salt = (salt * prime) & 0xFFFFFFFF
    }
    var posUint uint32
    posUint = uint32(position)
    var posMult uint32
    posMult = (posUint * 0xdeadbeef) & 0xFFFFFFFF
    var mixed uint32
    mixed = (salt ^ posMult) & 0xFFFFFFFF
    var shift uint32
    shift = mixed >> 16
    mixed = (mixed ^ shift) & 0xFFFFFFFF
    var keyByte byte
    keyByte = byte(mixed & 0xFF)
    var inputByte byte
    inputByte = c & 0xFF
    var result byte
    result = inputByte ^ keyByte
    return result
}

// Lightweight CRC-32 for PNG Chunk Compliance.
func ComputeCRC(buf []byte) uint32 {
    crc := uint32(0xFFFFFFFF)
    for _, b := range buf {
        crc ^= uint32(b)
        for j := 0; j < 8; j++ {
            // This matches the C++: (0xEDB88320 & (-(crc & 1)))
            mask := uint32(0)
            if crc&1 == 1 {
                mask = 0xEDB88320
            }
            crc = (crc >> 1) ^ mask
        }
    }
    return ^crc
}

func Write32(w io.Writer, val uint32) error {
    // Big-Endian byte order as required by PNG spec
    b := []byte{
        byte(val >> 24),
        byte(val >> 16),
        byte(val >> 8),
        byte(val),
    }
    _, err := w.Write(b)
    return err
}

func (s *ScyKernel) writeChunk(w io.Writer, name string, data []byte) {
    Write32(w, uint32(len(data)))
    
    // Chunk Name + Data combined for CRC calculation
    chunkType := []byte(name)
    w.Write(chunkType)
    w.Write(data)
    
    fullBuf := append(chunkType, data...)
    Write32(w, ComputeCRC(fullBuf))
}

// PPM sow, harvest functions
func (s *ScyKernel) PutToPPM(key, value, password string) {
	index := s.deriveIndex(key, password)
	curD := s.hVal + (index * 1600)
	var x, y int
	s.D2xy(s.canvasSize, curD, &x, &y)
	file, err := os.OpenFile(s.filePath, os.O_RDWR, 0644)
	if err != nil {
		fmt.Fprintf(os.Stderr, "❌ Error opening PPM: %v\n", err)
		return
	}
	defer file.Close()
	// Header offset (approx P6 PPM)
	offset := int64(15 + (y*s.canvasSize+x)*3)
	_, err = file.Seek(offset, 0)
	if err != nil {
		return
	}
	valBytes := []byte(value)
	for i := 0; i < len(valBytes); i++ {
		pixel := make([]byte, 3)
		// Read 3 bytes (the current pixel)
		_, err := file.Read(pixel)
		if err != nil {
			break
		}
		// Apply ScyKernel stream cipher before storage
		secureByte := CryptByte(valBytes[i], password, i)
		// Direct assignment to Red channel to match putToPNG logic
		pixel[0] = secureByte
		// Move back 3 bytes to overwrite the SAME pixel we just read
		_, err = file.Seek(-3, 1) // 1 = current position
		if err != nil {
			break
		}
		file.Write(pixel)
	}
	// Write Null Terminator (0, 0, 0)
	term := []byte{0, 0, 0}
	file.Write(term)
}

func (s *ScyKernel) GetFromPPM(key, password string) string {
	index := s.deriveIndex(key, password)
	curD := s.hVal + (index * 1600)
	var x, y int
	s.D2xy(s.canvasSize, curD, &x, &y)
	file, err := os.Open(s.filePath)
	if err != nil {
		return ""
	}
	defer file.Close()
	offset := int64(15 + (y*s.canvasSize+x)*3)
	_, err = file.Seek(offset, 0)
	if err != nil {
		return ""
	}
	var result []byte
	i := 0
	for {
		pixel := make([]byte, 3)
		_, err := file.Read(pixel)
		if err != nil || pixel[0] == 0 {
			break
		}
		scrambled := pixel[0]
		result = append(result, CryptByte(scrambled, password, i))
		i++
	}
	return string(result)
}

// PNG sow, harvest functions
/**
 * Writes a value to the RAM buffer.
 * Note: You MUST call SyncPNG(file, "commit") after calling this to save changes.
 */
 func (s *ScyKernel) PutToPNG(key, value, keyPassword string) {
	// Safety check: ensure buffer is initialized
	if len(s.dbBuffer) == 0 {
		s.dbBuffer = make([]byte, 48000000)
	}
	index := s.deriveIndex(key, keyPassword)
	curD := s.hVal + (index * 1600)
	var x, y int
	s.D2xy(s.canvasSize, curD, &x, &y)
	// Linear pixel walk in RAM
	valBytes := []byte(value)
	for i := 0; i < len(valBytes); i++ {
		pixelIdx := ((y * s.canvasSize) + (x + i)) * 3
		if pixelIdx+2 < len(s.dbBuffer) {
			secureByte := CryptByte(valBytes[i], keyPassword, i)
			// Direct assignment to Red Channel (Bit-perfect preservation)
			s.dbBuffer[pixelIdx] = secureByte
		}
	}
	// Write Null Terminator (0 in Red channel marks the end)
	termIdx := ((y * s.canvasSize) + (x + len(valBytes))) * 3
	if termIdx+2 < len(s.dbBuffer) {
		s.dbBuffer[termIdx] = 0
	}
}

/**
 * Retrieves a value from the RAM buffer.
 * Note: You SHOULD call SyncPNG(file, "load") before this to ensure fresh data.
 */
func (s *ScyKernel) GetFromPNG(key, keyPassword string) string {
	if len(s.dbBuffer) == 0 {
		return ""
	}
	index := s.deriveIndex(key, keyPassword)
	curD := s.hVal + (index * 1600)
	var x, y int
	s.D2xy(s.canvasSize, curD, &x, &y)
	var result []byte
	i := 0
	for {
		pixelIdx := ((y * s.canvasSize) + (x + i)) * 3
		// Bounds check + Null Terminator check (Red == 0)
		if pixelIdx+2 >= len(s.dbBuffer) || s.dbBuffer[pixelIdx] == 0 {
			break
		}
		scrambled := s.dbBuffer[pixelIdx]
		result = append(result, CryptByte(scrambled, keyPassword, i))
		i++
	}
	return string(result)
}

// DB sync functions for easier DB handling
func (s *ScyKernel) SyncPNG(filename string, mode string) bool {
	mode = strings.ToLower(mode)
	// Check if we are in LOAD MODE but the file is missing
	if mode == "load" {
		if _, err := os.Stat(filename); os.IsNotExist(err) {
			fmt.Println("⚠️ Database not found. Initializing new compressed store...")
			s.dbBuffer = make([]byte, 48000000)
			return s.SyncPNG(filename, "commit")
		}
	}
	if mode == "commit" { // COMMIT MODE (RAM -> Disk)
		filtered := make([]byte, 0, 48004000)
		for r := 0; r < 4000; r++ {
			filtered = append(filtered, 0) // Filter byte
			start := r * 12000
			end := start + 12000
			filtered = append(filtered, s.dbBuffer[start:end]...)
		}
		var b bytes.Buffer
		w := zlib.NewWriter(&b)
		w.Write(filtered)
		w.Close()
		compressed := b.Bytes()
		out, err := os.Create(filename)
		if err != nil {
			return false
		}
		defer out.Close()
		out.Write([]byte{0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A})
		ihdrBody := []byte{'I', 'H', 'D', 'R', 
			0, 0, 0x0F, 0xA0,
			0, 0, 0x0F, 0xA0,
			8, 2, 0, 0, 0}
		Write32(out, 13)
		out.Write(ihdrBody)
		Write32(out, ComputeCRC(ihdrBody))
		idatTag := []byte("IDAT")
		Write32(out, uint32(len(compressed)))
		out.Write(idatTag)
		out.Write(compressed)
		idatCrcBuf := append(idatTag, compressed...)
		Write32(out, ComputeCRC(idatCrcBuf))
		iendTag := []byte("IEND")
		Write32(out, 0)
		out.Write(iendTag)
		Write32(out, ComputeCRC(iendTag))
		fmt.Printf("✅ PNG Commit Successful: %s\n", filename)
		return true
	} else if mode == "load" { // LOAD MODE (Disk -> RAM)
		file, err := os.Open(filename)
		if err != nil {
			return false
		}
		defer file.Close()
		file.Seek(33, 0)
		var cLen uint32
		binary.Read(file, binary.BigEndian, &cLen)
		file.Seek(4, 1)
		cData := make([]byte, cLen)
		file.Read(cData)
		reader, err := zlib.NewReader(bytes.NewReader(cData))
		if err != nil {
			return false
		}
		defer reader.Close()
		decomp := make([]byte, 48004000)
		io.ReadFull(reader, decomp)
		s.dbBuffer = make([]byte, 48000000)
		for r := 0; r < 4000; r++ {
			copy(s.dbBuffer[r*12000:], decomp[r*12001+1 : r*12001+12001])
		}
		//fmt.Printf("✅ PNG Load Successful: %s\n", filename)
		return true
	}
	return false
}

func (s *ScyKernel) SyncPPM(filename string, mode string) bool {
	mode = strings.ToLower(mode)
	// Check if we are in LOAD MODE but the file is missing
	if mode == "load" {
		if _, err := os.Stat(filename); os.IsNotExist(err) {
			fmt.Println("⚠️ PPM Database not found. Initializing new raw store...")
			s.dbBuffer = make([]byte, 48000000)
			return s.SyncPPM(filename, "commit")
		}
	}
	if mode == "commit" { // COMMIT MODE (RAM -> Disk)
		out, err := os.Create(filename)
		if err != nil {
			return false
		}
		defer out.Close()
		header := fmt.Sprintf("P6\n%d %d\n255\n", s.canvasSize, s.canvasSize)
		out.WriteString(header)
		out.Write(s.dbBuffer)
		fmt.Printf("✅ PPM Commit Successful: %s\n", filename)
		return true
	} else if mode == "load" { // LOAD MODE (Disk -> RAM)
		file, err := os.Open(filename)
		if err != nil {
			return false
		}
		defer file.Close()
		file.Seek(15, 0)
		s.dbBuffer = make([]byte, 48000000)
		io.ReadFull(file, s.dbBuffer)
		fmt.Printf("✅ PPM Load Successful: %s\n", filename)
		return true
	}
	return false
}

// Blank DB creation functions
func (s *ScyKernel) CreatePNG_DB(filename string) {
	s.dbBuffer = make([]byte, 48000000)
	if s.SyncPNG(filename, "commit") {
		fmt.Printf("✅ PNG initialized and loaded into buffer: %s\n", filename)
	} else {
		fmt.Fprintf(os.Stderr, "❌ Failed to initialize PNG database file.\n")
	}
}

func (s *ScyKernel) CreatePPM_DB(dbPath string) {
	ofs, err := os.Create(dbPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "❌ Error: Could not create PPM database: %v\n", err)
		return
	}
	defer ofs.Close()
	// Write the P6 Header (Standard 4000x4000 8-bit RGB)
	header := fmt.Sprintf("P6\n%d %d\n255\n", s.canvasSize, s.canvasSize)
	ofs.WriteString(header)
	zeroRow := make([]byte, s.canvasSize*3)
	for i := 0; i < s.canvasSize; i++ {
		_, err := ofs.Write(zeroRow)
		if err != nil {
			fmt.Fprintf(os.Stderr, "❌ Error writing to PPM: %v\n", err)
			return
		}
	}
	fmt.Printf("✅ PPM Database Ready (Isolated from RAM): %s\n", dbPath)
}

// DB conversion functions
func (s *ScyKernel) ConvertDatabaseFormat(pngPath string, ppmPath string, targetFormat string) bool {
	// Standardize the flag to lowercase
	targetFormat = strings.ToLower(targetFormat)
	if targetFormat == "ppm" {
		// SOURCE: PNG -> TARGET: PPM (Decompress and Expand)
		if !s.SyncPNG(pngPath, "load") {
			fmt.Println("❌ Failed to load PNG database.")
			return false
		}
		ppm, err := os.Create(ppmPath)
		if err != nil {
			return false
		}
		defer ppm.Close()
		// Write P6 PPM Header (Standard 4000x4000 8-bit)
		header := "P6\n4000 4000\n255\n"
		_, err = ppm.WriteString(header)
		if err != nil {
			return false
		}
		// Dump the raw 48MB buffer into the file
		_, err = ppm.Write(s.dbBuffer)
		if err != nil {
			return false
		}
		fmt.Println("✅ Converted PNG to PPM (48MB Raw Volume)")
		return true
	} else if targetFormat == "png" {
		// SOURCE: PPM -> TARGET: PNG (Pack and Compress)
		ppm, err := os.Open(ppmPath)
		if err != nil {
			return false
		}
		defer ppm.Close()
		// Skip the header (Assuming 15 bytes)
		_, err = ppm.Seek(15, 0)
		if err != nil {
			return false
		}
		const rawSize = 48000000
		// Read the raw 48MB into our RAM buffer
		s.dbBuffer = make([]byte, rawSize)
		_, err = ppm.Read(s.dbBuffer)
		if err != nil {
			return false
		}
		// Use SyncPNG to compress and save
		if !s.SyncPNG(pngPath, "commit") {
			fmt.Println("❌ Failed to compress and save PNG database.")
			return false
		}
		fmt.Println("✅ Converted PPM to PNG")
		return true
	} else {
		fmt.Println("❌ Invalid target format. Use 'PNG' or 'PPM'.")
		return false
	}
}

// DB Deletion and cleanup functions
func (k *ScyKernel) DeleteDB(path string) error {
    return os.Remove(path)
}

// DB checking/validating functions
func (s *ScyKernel) GetFileSize(path string) int64 {
	info, err := os.Stat(path)
	if err != nil {
		return 0
	}
	if info.Mode().IsRegular() {
		return info.Size()
	}
	return 0
}

func (s *ScyKernel) ValidateDB(path string) bool {
	// 4000 * 4000 * 3
	const rawDataSize int64 = 48000000
	actual := s.GetFileSize(path)
	if strings.Contains(path, ".ppm") {
		// PPM must have the header + the data (Header is ~15 bytes)
		return actual >= (rawDataSize + 15)
	} else {
		// PNG/Raw must be at least the data size
		return actual >= rawDataSize
	}
}