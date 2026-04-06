package main

import (
	"fmt"
	"os"
)

func main() {
	password := "ScyWeb_Global_Secret_2026"
	imagePath := "../../vines_images/parity_test.ppm"
	
	testKey := "user"
	testValue := "Amanda"

	// Ensure PPM exists for testing
	if _, err := os.Stat(imagePath); os.IsNotExist(err) {
		f, _ := os.Create(imagePath)
		f.Write([]byte("P6\n4000 4000\n255\n"))
		empty := make([]byte, 4000*4000*3)
		f.Write(empty)
		f.Close()
	}

	kernel := NewScyKernel(password, imagePath)

	fmt.Printf("Go: Putting key '%s' with value '%s'...\n", testKey, testValue)
	err := kernel.Put(testKey, testValue)
	if err != nil {
		fmt.Printf("❌ Go Error: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Go: Getting key '%s'...\n", testKey)
	result, err := kernel.Get(testKey)
	if err != nil {
		fmt.Printf("❌ Go Error: %v\n", err)
		os.Exit(1)
	}

	if result == testValue {
		fmt.Printf("✅ Go KV Parity: SUCCESS (Recovered: %s)\n", result)
		os.Exit(0)
	} else {
		fmt.Printf("❌ Go KV Parity: FAIL\nExpected: %s, Got: %s\n", testValue, result)
		os.Exit(1)
	}
}