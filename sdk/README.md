# ScyWeb SDK | An Image Database Solution
**Lead Architect:** Matthew D. Benchimol  
**Protocol Version:** ? (Geometric Entropy)  
**Audit Date:** April 2026

![ScyWeb SDK Logo](https://raw.githubusercontent.com/mdbench/ScyWeb/master/sdk/logo.png)

This directory contains the **ScyWeb SDK**. By utilizing **Vectorial Normalization** and **Space-Filling Curves**, ScyWeb turns standard high-resolution images into high-entropy, decentralized databases with different checksums that produce the same results, making them immune to traditional file-checking de-raveling schemes while having simultaneous data parity. The ultimate goal of the SDK tests is to prove that the ScyWeb "Vine" architecture generates mathematically identical image-databases across ten different programming languages. Data sowed in **Java** can be harvested by **C++**, **Swift**, or **PHP** with zero bit-drift. 

## The ScyWeb SDK Methodology: Geometric Entropy

The ScyWeb SDK treats a 4000x4000 pixel image (16,000,000 pixels) as a coordinate-mapped grid. This size constraint creates a modular architecture. Spin one up when you need it and down when you don't, knowing the size is capped, keeping your database small and lightweight. At a 48MB cap, you will likely never notice the size constraints and if you do you can create another database easily. You can even create a database as a pointer to your other databases so you can find them when you need them or you can just hardcode the paths into your projects accordingly. This flexibility is paramount to highly structured and unstructured data. 

There are two types of ScyWeb SDK databases: PPM and PNG. PPM represents an exact coordinate map of an image. It is literally a textual version of an image. PNG represents a literal image. In memory, both are mapped in the same way to represent an image. However, the PNG version is drastically smaller when compressed. When both files have similar data, the PNG database is 750% smaller than the PPM database. Both are drastically smaller than databases you can implement in your project and both are better for cloud storage due to their modular nature, small sizes, and low overhead. Both databases are NoSQL databases that utilize a key/value storage framework. Eventually, an SQL wrapper might be added but honestly SQL just does not make sense anymore now that this SDK is available.

A core goal of this SDK is data availability so data created in any language needs to be able to access data created from another language. This allows developers to create better data pipelines and storage frameworks. The only way to achieve this is to ensure data "sows" properly across multiple languages without collisions. We call it sowing because you are using a complicated hashing methodology to place a database entry using its key as a derivative password at a coordinate derived from a Hilbert fractal that was seeded psuedo-randomly. This means only you can harvest your garden for the fruits of your labor. To further this effect of randomness and security, each database entry is encrypted with bit-for-bit parity, ensuring the file size does not increase while enhancing the full effects of the sow-to-harvest methodology.

Data availability is part of a **10-Language Parity** method. One goal of this SDK is to allow C++, GO, Java, Node.js, Kotlin, PHP, Python, React-Native, Rust, and Swift to sow and harvest from any database created or modified by its farm team language. Essentially, the image database is the farm and each language needs to be able to pitch hit when called up without any errors or problems on the fly. This allows projects with better support for specific methods or frameworks to be used in tandem with other languages. To do this, the SDK needed more than a sow-to-harvest methodology. It needs backstops. A deterministic projection model using vectorial normalization with a vines architecture was created. The explanations are below...

### Vectorial Normalization
Instead of simple remainders, the ScyWeb SDK uses **Vectorial Normalization** to map a 32-bit FNV-1a hash into a coordinate space. This ensures a perfectly linear distribution of data across the 16M (4000x4000) pixel canvas. Usually, you do not want to use a partially deterministic hash, as its determinism can be used to reverse engineer its position but this was necessary to prevent data writing overlaps and allows for a theoretical maximum of 10,000 records with 4.8KBs per record at a less than 1% likelihood for a collision (data overlap). The equation that derives the space within normalized limits is below.

$$Index = \lfloor (\frac{\text{unsigned } Hash}{2^{32}}) \times 16,000,000 \rfloor$$

> **Note:** Because the number of pixels is so high for each database, there is a data trap problem for bad actors attempting to process pixels for reverse engineering purposes. This data trap is even intractable for even quantum computers, making the deterministic hash insecure normally but extremely secure in the sow-to-harvest methodology.

### The "Vine" Architecture
A **Vine** is a self-terminating, high-capacity data sequence. Unlike standard steganography, ScyWeb SDK provides a dedicated, sequential buffer for every entry.

* **Sequential Packing**: Each vine is allocated **1,600 pixels (4.8 KB)** of contiguous space. This multiplier ensures that up to **10,000 unique records** can be sowed without a single pixel collision.
* **Fractal Traversal**: The 1D index is mapped to 2D $(x, y)$ coordinates using **Hilbert Space-Filling Curves**. This preserves spatial locality and ensures that data remains geometrically structured yet visually indistinguishable from noise.
* **XOR Obfuscation**: Payloads are XORed directly into the Red channel of the image, making the database appear as high-entropy "grain" to any viewer.
* **Autonomous Termination**: Records are null-terminated (`\0`). This allows any kernel to harvest data without needing a centralized File Allocation Table (FAT) or external metadata.

---

## Supported Kernels

The following kernels have been synchronized for bit-perfect parity, regardless of the underlying memory model or integer-handling behavior (32-bit vs 64-bit).

| Kernel | Runtime/Compiler | Status | Parity Method |
| :--- | :--- | :--- | :--- |
| **CPP** | g++ 11+ | ? | Native `uint32_t` |
| **RUST** | rustc 1.70+ | ? | `wrapping_mul` / `u32` |
| **JAVA** | OpenJDK 17+ | ? | Masked `Long` Parity |
| **NODE** | Node.js 20+ | ? | `Math.imul` / `>>> 0` |
| **PYTHON** | Python 3.10+ | ? | `ctypes.c_uint32` |
| **GO** | Go 1.21+ | ? | Native `uint32` |
| **SWIFT** | Swift 5.9+ | ? | `UInt32` Overflow Ops |
| **PHP** | PHP 8.2+ | ? | `& 0xFFFFFFFF` Masking |
| **KOTLIN** | Kotlin 1.9+ | ? | `UInt` / `toLong` |
| **RN** | Hermes/V8 | ? | Polyfilled Buffer/FS |

---

## Integration Guide
Developers can integrate any SDK ScyKernel to create a cross-platform hidden database. To maintain cross-language parity, use these official integration methods. This allows you to receive critical updates (like the v2.5 Vectorial Normalization) with a single command.

---

### Package Manager Integration

| Language | Method | Command / Config |
| :--- | :--- | :--- |
| **Node.js** | NPM | `npm install github:mdbench/ScyWeb#subdirectory=sdk/javascript` |
| **Go** | Go Modules | `go get github.com/mdbench/ScyWeb/sdk/go` |
| **Rust** | Cargo | `scyweb = { git = "https://github.com/mdbench/ScyWeb" }` |
| **Python** | Pip | `pip install git+https://github.com/mdbench/ScyWeb.git#subdirectory=sdk/python` |
| **PHP** | Composer | `composer require mdbench/scyweb-php:dev-main` |
| **Swift** | Swift PM | Add `https://github.com/mdbench/ScyWeb` via Xcode Packages |
| **React Native**| NPM | `npm install github:mdbench/ScyWeb#subdirectory=sdk/react-native` |

---

### Manual Class Integration

If you prefer not to use a package manager, copy the kernel file directly into your source tree.

#### Systems & Compiled
* **C++:** Copy `ScyKernel.hpp`. Usage: `ScyKernel kernel("pass", "db.ppm");`
* **Rust:** Copy `scy_kernel.rs`. Usage: `mod scy_kernel; use scy_kernel::ScyKernel;`
* **Swift:** Drag `ScyKernel.swift` to Xcode. Usage: `let k = ScyKernel(password: "p", filePath: "f")`
* **Go:** Copy `scy_kernel.go`. Usage: `k := NewScyKernel("pass", "db.ppm")`

#### Web & Scripting
* **Node.js:** Copy `ScyKernel.js`. Usage: `const ScyKernel = require('./ScyKernel');`
* **Python:** Copy `scy_kernel.py`. Usage: `from scy_kernel import ScyKernel`
* **PHP:** Require `ScyKernel.php`. Usage: `$k = new ScyKernel("pass", "db.ppm");`

#### 🔄 Updating
When logic updates are pushed to the main repository, update your local SDK via:
* **NPM:** `npm update`
* **Go:** `go get -u ./...`
* **Python:** `pip install --upgrade git+https://github.com/mdbench/ScyWeb.git#subdirectory=sdk/python`
* **Composer:** `composer update`

---

### Live Interactive Demo
This demo serves as a **High-Correlation Stress Test** for the ScyWeb cryptographic image database kernel. Unlike standard encryption tests that use high-entropy keys, this demo uses a sequence of nearly identical, low-distance derivatives (**Test1** through **Test10000**) to stress test potential collisions or data overlap problems. These demos will not work with SDK databases you are making. The are for illustration purposes and proof. 
- [Demo](https://demos.matthewbenchimol.com/ScyWeb/sdk/ScyWebSDKDemo.html)
    - Take [scy_demo_database.ppm](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/sdk/scy_demo_database.ppm) and load it into the SDK Demo to see that you can query an image database using NoSQL key/value.
    - How to Run the Diagnostic:
        1. **Open the Live Demo URL** in a Chromium-based browser.
        2. **Mount Database:** Click the "Mount" button and select the downloaded `scy_demo_database.ppm`.
        3. **Set Credentials:** Enter the System Seed: `password123`.
        4. **Initiate Harvest:** Run the **Batch Integrity Scan** to observe the real-time harvest of 10,000 vines across the Hilbert-mapped canvas.
- [Demo](https://demos.matthewbenchimol.com/ScyWeb/sdk/ScyWebDatabaseCompressor.html)
    - Take [scy_demo_database.ppm](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/sdk/scy_demo_database.ppm), map it to space, and convert it to a .scy file to see the database get compressed from 45.8MBs to 2.8MBs, making it 150% smaller.
    - Take [scy_demo_database.ppm](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/sdk/scy_demo_database.ppm), map it to space, and export it to a png image file to see the database get compressed from 45.8MBs to 714KBs, making it 6,353.5% smaller.
    - Take [scy_demo_database.png](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/sdk/scy_demo_database.png) and map it to space, convert it to .scy, and convert it back to a .ppm file to see no data was lost.
    - A lossless strictly image version called [scy_demo_database_lossless_compressed.png](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/sdk/scy_demo_database_lossless_compressed.png) shows a file size of 95KBs, making it 750% smaller than its predecessor with no data loss.

### Here is what an image database looks like as a PNG (sdk/scy_demo_database.png)
<img src="https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/sdk/scy_demo_database.png" width="400" height="400">

### Benchmark Methodology: Explaining how the "Worst Case Scenario" was created
The **High-Correlation Stress Test** methodology and results are below:

* **The Input:** 10,000 keys with >90% bit-structure similarity (`Test1` through `Test10000`).
* **The Constraint:** In a 4000x4000 grid, every pixel represents a mapping bucket for ~268 possible 32-bit hash values.
* **The Result:** A **~96% Integrity Rate**. 
* **The Technical Conclusion:** The observed 4% collision rate is a "Similarity Tax" imposed by the adversarial nature of the keys. Under standard operating conditions (diverse, high-entropy passphrases or UUIDs), the kernel's distribution uniformity naturally approaches **99%—100%**.

---