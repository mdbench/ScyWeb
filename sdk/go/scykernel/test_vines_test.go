package scykernel

import (
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"testing"
)

func TestVinesParity(t *testing.T) {
	const dir = "vines_images"
	path := filepath.Join(dir, "go_vine.ppm")
	path2 := filepath.Join(dir, "go_vine.png")
	const testKey = "User"
	const testValue = "Amanda"
	const password = "ScyWeb_Global_Secret_2026"

	// Ensure the local folder exists
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		_ = os.MkdirAll(dir, 0755)
	}

	// Instantiating 'scy' (Internal package access)
	scy := NewScyKernel(password, path)

	// Creating the test DBs
	scy.CreatePPM_DB(path)
	scy.SyncPNG(path2, "load")

	// Test both PPM and PNG DBs
	scy.PutToPPM(testKey, testValue, password)
	scy.PutToPNG(testKey, testValue, password)

	// sync changes and refresh
	scy.SyncPNG(path2, "commit")
	scy.SyncPNG(path2, "load")

	// Retrieve the results from both DBs
	result := scy.GetFromPPM(testKey, password)
	result2 := scy.GetFromPNG(testKey, password)

	// Output Comparison
	if result == testValue && result2 == testValue {
		validationTest := "Invalid"
		if scy.ValidateDB(path) {
			validationTest = "Valid"
		}
		fmt.Printf("✅ Go KV Parity: SUCCESS (Recovered: %s)\n", result)
		fmt.Printf("🧩 PPM is: %s\n", validationTest)
		info, err := os.Stat(path2)
		if err == nil {
			sizeStr := strconv.FormatInt(info.Size(), 10) + " bytes"
			fmt.Printf("📏 Size of Image DB: %s\n", sizeStr)
		}
		type parityConfig struct {
			lang string
			path string
		}
		configs := []parityConfig{
			{"C++", "../../cpp/vines_images/cpp_vine.png"},
			{"Go", "../../go/scykernel/vines_images/go_vine.png"},
			{"Java", "../../java/vines_images/java_vine.png"},
			{"Node", "../../javascript/vines_images/node_vine.png"},
			{"Kotlin", "../../kotlin/vines_images/kt_vine.png"},
			{"PHP", "../../php/vines_images/php_vine.png"},
			{"Python", "../../python/vines_images/py_vine.png"},
			{"React Native", "../../react-native/vines_images/rn_vine.png"},
			{"Rust", "../../rust/vines_images/rust_vine.png"},
			{"Swift", "../../swift/vines_images/swift_vine.png"},
		}
		for _, cfg := range configs {
			if _, err := os.Stat(cfg.path); err == nil {
				scyCheck := NewScyKernel(password, cfg.path)
				if scyCheck.SyncPNG(cfg.path, "load") {
					res := scyCheck.GetFromPNG(testKey, password)
					if res == testValue {
						fmt.Printf("✅ Go to %s Parity: SUCCESS (Recovered: %s)\n", cfg.lang, res)
					} else {
						fmt.Printf("❌ Go to %s Parity: FAIL\n", cfg.lang)
					}
				}
			}
		}
		//os.Remove(path)
		//os.Remove(path2)
	} else {
		fmt.Printf("❌ Go KV Parity: FAIL\n")
		fmt.Printf("Expected: %s, Got: [%s]\n", testValue, result)
		fmt.Printf("Expected: %s, Got: [%s]\n", testValue, result2)
		os.Remove(path)
		os.Remove(path2)
		t.Fail()
	}
}