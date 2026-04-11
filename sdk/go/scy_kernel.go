package main

import (
	"io"
	"os"
	"strings"
	"math"
	"unicode"
)

type ScyKernel struct {
	password   string
	filePath   string
	hVal       int
	canvasSize int
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
	hash := 7
	for _, c := range pwd {
		hash = hash*31 + int(c)
	}
	if hash < 0 {
		hash = -hash
	}
	return int((float64(hash) / 4294967296.0) * 16000000)
}

// Manual FNV-1a + Alphabet Salt for Cross-Language Parity
func (k *ScyKernel) deriveIndex(key string, password string) int {
	var hash uint32 = 0x811c9dc5
	var prime uint32 = 0x01000193
	var alphaSalt int64 = 0

	if password != "" {
		for _, c := range password {
			hash ^= uint32(c)
			hash *= prime
		}
	}

	for _, c := range key {
		// FNV-1a
		hash ^= uint32(c)
		hash *= prime
		// Alphabet Salt
		if unicode.IsLetter(c) {
			alphaSalt += int64(unicode.ToLower(c) - 'a' + 1)
		}
	}
	
	finalVal := uint32(int64(hash) + alphaSalt)
	
	normalized := (float64(finalVal) / 4294967296.0) * 16000000.0
	return int(math.Floor(normalized))
}

func (k *ScyKernel) rot(n, x, y, rx, ry int) (int, int) {
	if ry == 0 {
		if rx == 1 {
			x = n - 1 - x
			y = n - 1 - y
		}
		return y, x
	}
	return x, y
}

func (k *ScyKernel) d2xy(n, d int) (int, int) {
	x, y := 0, 0
	t := d
	for s := 1; s < n; s *= 2 {
		rx := 1 & (t / 2)
		ry := 1 & (t ^ rx)
		x, y = k.rot(s, x, y, rx, ry)
		x += s * rx
		y += s * ry
		t /= 4
	}
	return x, y
}

func (k *ScyKernel) Put(key, value, password string) error {
	index := k.deriveIndex(key, password)
	curD := k.hVal + (index * 1600)
	x, y := k.d2xy(k.canvasSize, curD)

	file, err := os.OpenFile(k.filePath, os.O_RDWR, 0644)
	if err != nil {
		return err
	}
	defer file.Close()

	// P6 Header Offset (~15 bytes)
	offset := int64(15 + (y*k.canvasSize+x)*3)
	
	for i := 0; i < len(value); i++ {
		file.Seek(offset+(int64(i)*3), 0)
		pixel := make([]byte, 3)
		file.Read(pixel)
		
		pixel[0] ^= value[i] // XOR Obfuscation
		
		file.Seek(offset+(int64(i)*3), 0)
		file.Write(pixel)
	}

	// Write Null Terminator
	file.Seek(offset+(int64(len(value))*3), 0)
	file.Write([]byte{0, 0, 0})
	return nil
}

func (k *ScyKernel) Get(key, password string) (string, error) {
	index := k.deriveIndex(key, password)
	curD := k.hVal + (index * 1600)
	x, y := k.d2xy(k.canvasSize, curD)

	file, err := os.Open(k.filePath)
	if err != nil {
		return "", err
	}
	defer file.Close()

	offset := int64(15 + (y*k.canvasSize+x)*3)
	var result strings.Builder

	for i := 0; ; i++ {
		file.Seek(offset+(int64(i)*3), 0)
		pixel := make([]byte, 3)
		_, err := file.Read(pixel)
		if err == io.EOF || pixel[0] == 0 {
			break
		}
		result.WriteByte(pixel[0])
	}
	return result.String(), nil
}

func (k *ScyKernel) DeleteDB(path string) error {
    return os.Remove(path)
}