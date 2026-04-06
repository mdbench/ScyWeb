# ScyWeb SDK | An Image Database Solution
**Lead Architect:** Matthew D. Benchimol  
**Protocol Version:** ? (Geometric Entropy)  
**Audit Date:** April 2026

This directory contains the **Cross-Kernel Parity Engine**. The purpose of these tests is to prove that the ScyWeb "Vine" architecture generates mathematically identical image-databases across ten different programming languages that have different checksums, making them immune to file checking de-raveling schemes. Data sowed in **Java** can be harvested by **C++** or **Node.js** with zero bit-drift.

---

## 📂 Directory Structure

* **`tests/parity_check.sh`**: An orchestration script representing the original method, executing all 10 kernels (collision unsafe).
* **`tests/parity_images/`**: A folder storing `.ppm` database files from the parity_check.sh script for harvest checking (auto-generated).
* **`tests/vines_check.sh`**: An orchestration script representing the final method, executing all 10 kernels (collision safe).
* **`tests/vines_images/`**: A folder storing `.ppm` database files from the vines_check.sh script for harvest checking (auto-generated).
* **`tests/visual_db.sh`**: An orchestration script to convert all `.ppm` database files to a `.png` to prove image is database.
* **`tests/visual_audits/`**: A folder storing `.png` database files from the parity_check.sh and vines_check.sh script after running visual_db.sh.

---

## 🧪 The Vine Method: How it Works

The ScyWeb SDK treats a 4000x4000 pixel image as a coordinate-mapped grid. To achieve **10-Language Parity**, we use a standardized coordinate extraction method that remains consistent regardless of the underlying memory model.

### 1. Hex-Coordinate Mapping
Every data record is sowed at a specific $(x, y)$ coordinate derived from a SHA-256 hash. We use a **16-bit split** to ensure the math remains consistent across 32-bit and 64-bit systems.

$$Hash = \text{SHA-256}(Prefix + ID + Salt)$$
$$x = \text{int}(Hash[0:4], 16) \pmod{4000}$$
$$y = \text{int}(Hash[4:8], 16) \pmod{4000}$$

### 2. The Vines Method
Unlike standard steganography which often uses LSB replacement in a linear fashion, a **Vine** is a self-terminating data sequence that "grows" through the coordinate space.

* **Sowing**: The kernel starts at the calculated $(x, y)$ and writes the payload in 3-byte RGB chunks.
* **Traversal**: The pointer moves to the next pixel for each chunk, following a deterministic path (e.g., Hilbert Curve or incremental step).
* **Termination**: A `\0` null-terminator is injected at the end of the string. This allows any harvester to extract the record without needing a centralized file allocation table (FAT).

---

## 🛠 Supported Kernels

| Kernel | Runtime/Compiler | Method |
| :--- | :--- | :--- |
| **CPP** | g++ (libcrypto) | Native Binary |
| **RUST** | rustc (sha2) | System Native |
| **JAVA** | javac (MessageDigest) | JVM |
| **NODE** | node (crypto) | V8 Engine |
| **PYTHON** | python3 (hashlib) | Interpreted |
| **GO** | go run (crypto/sha256) | Compiled |
| **SWIFT** | swift (CommonCrypto) | Native |
| **PHP** | php (hash) | CLI |
| **KOTLIN** | kotlinc | JVM Script |
| **RN** | node (Simulated) | Mobile Standard |

---