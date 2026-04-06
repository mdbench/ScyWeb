import os
import sys
from scy_kernel import ScyKernel

def main():
    password = "ScyWeb_Global_Secret_2026"
    image_path = "../../vines_images/parity_test.ppm"
    
    test_key = "user"
    test_value = "Amanda"

    try:
        # Ensure PPM exists for testing
        if not os.path.exists(image_path):
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            with open(image_path, "wb") as f:
                f.write(b"P6\n4000 4000\n255\n")
                # Pre-allocate 48MB of null bytes
                f.write(b"\x00" * (4000 * 4000 * 3))

        kernel = ScyKernel(password, image_path)

        print(f"Python: Putting key '{test_key}'...")
        kernel.put(test_key, test_value)

        print(f"Python: Getting key '{test_key}'...")
        result = kernel.get(test_key)

        if result == test_value:
            print(f"✅ Python KV Parity: SUCCESS (Recovered: {result})")
            sys.exit(0)
        else:
            print(f"❌ Python KV Parity: FAIL")
            print(f"Expected: {test_value}, Got: {result}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Python Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()