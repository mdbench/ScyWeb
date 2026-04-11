import os
import sys
from ScyKernel import ScyKernel

def run_test():
    test_key = "User"
    test_value = "Amanda"
    password = "ScyWeb_Global_Secret_2026"
    db_dir = "vines_images"
    db_path = os.path.join(db_dir, "py_vine.ppm")

    # PHYSICAL FILE SETUP
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    try:
        with open(db_path, "wb") as f:
            # Exact 15-byte header parity: "P6 4000 4000 25"
            header = b"P6 4000 4000 255\n"
            f.write(header[:15])
            
            # Allocate 48MB (4000 * 4000 * 3 + 15)
            f.truncate(48000015)
    except Exception as e:
        print(f"❌ Failed to create database file: {e}")
        sys.exit(1)

    # INITIALIZE KERNEL
    scy = ScyKernel(password, db_path)

    # SOW: Put operation (Must use 1600 offset internally)
    try:
        scy.put(test_key, test_value, password)
    except Exception as e:
        print(f"❌ Python SDK Put Error: {e}")
        if os.path.exists(db_path):
            os.remove(db_path)
        sys.exit(1)

    # HARVEST: Get operation
    try:
        result = scy.get(test_key, password)

        if result == test_value:
            print(f"✅ Python KV Parity: SUCCESS (Recovered: {result})")
            scy.delete_db(db_path)
            sys.exit(0)
        else:
            print("❌ Python KV Parity: FAIL")
            print(f"Expected: {test_value}, Got: [{result}]")
            scy.delete_db(db_path)
            sys.exit(1)
    except Exception as e:
        print(f"❌ Python SDK Get Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_test()