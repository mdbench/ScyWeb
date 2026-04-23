import os
import sys
from ScyKernel import ScyKernel

def run_test():
    db_dir = "vines_images"
    path_ppm = os.path.join(db_dir, "py_vine.ppm")
    path_png = os.path.join(db_dir, "py_vine.png")
    test_key = "User"
    test_value = "Amanda"
    #test_value = "<bos> " + ("STRESS_TEST_DATA_" * 280) + " <eos>"
    password = "ScyWeb_Global_Secret_2026"
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    scy = ScyKernel(password, path_ppm)
    scy.create_ppm_db(path_ppm)
    scy.sync_png(path_png, "load")
    scy.put_to_ppm(test_key, test_value, password)
    scy.put_to_png(test_key, test_value, password)
    scy.sync_png(path_png, "commit")
    scy.sync_png(path_png, "load")
    result_ppm = scy.get_from_ppm(test_key, password)
    result_png = scy.get_from_png(test_key, password)
    if result_ppm == test_value and result_png == test_value:
        validation = "Valid" if scy.validate_db(path_ppm) else "Invalid"
        print(f"✅ Python KV Parity: SUCCESS (Recovered: {result_ppm})")
        print(f"🧩 PPM is: {validation}")
        print(f"📏 Size of Image DB: {scy.get_file_size(path_png)} bytes")
        parity_configs = [
            ("C++", "../cpp/vines_images/cpp_vine.png"),
            ("Go", "../go/scykernel/vines_images/go_vine.png"),
            ("Java", "../java/vines_images/java_vine.png"),
            ("Node", "../javascript/vines_images/node_vine.png"),
            ("Kotlin", "../kotlin/vines_images/kt_vine.png"),
            ("PHP", "../php/vines_images/php_vine.png"),
            ("Python", "../python/vines_images/py_vine.png"),
            ("React Native", "../react-native/vines_images/rn_vine.png"),
            ("Rust", "../rust/vines_images/rust_vine.png"),
            ("Swift", "../swift/vines_images/swift_vine.png")
        ]
        for lang, l_path in parity_configs:
            if os.path.exists(l_path):
                if scy.sync_png(l_path, "load"):
                    res = scy.get_from_png(test_key, password)
                    if res == test_value:
                        print(f"✅ Python to {lang} Parity: SUCCESS (Recovered: {res})")
                    else:
                        print(f"❌ Python to {lang} Parity: FAIL")
        sys.exit(0)
    else:
        print("❌ Python KV Parity: FAIL")
        print(f"Expected: {test_value}, Got PPM: [{result_ppm}], PNG: [{result_png}]")
        scy.delete_db(path_ppm)
        scy.delete_db(path_png)
        sys.exit(1)

if __name__ == "__main__":
    run_test()