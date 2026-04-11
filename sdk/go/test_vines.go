package main

import (
	"fmt"
	"os"
)

func main() {

	const testKey = "User"
	const testValue = "Amanda"
	const password = "ScyWeb_Global_Secret_2026"
	const dbPath = "vines_images/go_vine.ppm"

	_ = os.Mkdir("vines_images", 0755)
	f, err := os.Create(dbPath)
	if err != nil {
		fmt.Printf("❌ IO Error: %v\n", err)
		os.Exit(1)
	}
	
	// Exact 15-byte header: "P6 4000 4000 255\n" truncated to 15
	header := []byte("P6 4000 4000 255\n")
	f.Write(header[:15])
	f.Truncate(48000015)
	f.Close()

	// Ensure NewScyKernel and its methods are visible in the main package
	scy := NewScyKernel(password, dbPath)

	// SOW: Put operation (uses 1600 offset)
	if err := scy.Put(testKey, testValue, password); err != nil {
		fmt.Printf("❌ Put Error: %v\n", err)
		os.Remove(dbPath)
		os.Exit(1)
	}

	// HARVEST: Get operation (uses 1600 offset)
	result, err := scy.Get(testKey, password)
	if err != nil {
		fmt.Printf("❌ Get Error: %v\n", err)
		os.Remove(dbPath)
		os.Exit(1)
	}

	if result == testValue {
		fmt.Printf("✅ Go KV Parity: SUCCESS (Recovered: %s)\n", result)
		scy.DeleteDB(dbPath)
		os.Exit(0)
	} else {
		fmt.Printf("❌ Go KV Parity: FAIL\n")
		fmt.Printf("Expected: %s, Got: [%s]\n", testValue, result)
		scy.DeleteDB(dbPath)
		os.Exit(1)
	}
}