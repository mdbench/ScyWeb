# CalcTale Sovereign Core: MZMO Forensic Data Architecture

The CalcTale Sovereign Core is a high-precision data processing platform designed to transcend the limitations of traditional spreadsheet and database software. It utilizes a proprietary MZMO (Morton-Z Matrix Object) image-based storage methodology to encode IEEE 754 Double-Precision (64-bit) data into lossless PNG matrices.

## Working paper
- [Future academic submission as PDF](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/calctale/WorkingPaper.pdf)
- [LaTeX submission version](https://raw.githubusercontent.com/mdbench/ScyWeb/refs/heads/main/calctale/WorkingPaper.tex)

The demos can be accessed online from a unified dashboard here:
    - [CalcTale](https://demos.matthewbenchimol.com/ScyWeb/calctale/index.html)
    - Or, just clone this git and use it entirely offline (recommended) by opening each of the pages: engineer.html, physics.html, and statistics.html.

## System Overview

CalcTale operates as a sovereign, browser-based workstation. It requires no server-side processing, ensuring that sensitive engineering and physics data remains entirely within the user's local file system.

### Core Disciplines
* **Engineering Suite:** Focuses on structural integrity, calculating Stress (F/A) and Strain (dL/L) with bit-perfect traceability.
* **Physics Suite:** Executes universal constant calculations, including Mass-Energy Equivalence (E=mc²), Newtonian Gravitation (F=GmM/r²), and Schwarzschild Radius (Rs=2GM/c²) determinations.
* **Statistics Suite:** Conducts Ordinary Least Squares (OLS) and Logistic regression analysis, allowing an unlimited amount of data ingestion from a CSV and subsequent calculations. N of 27million+ took approximately 50 seconds.

## The MZMO Methodology

Traditional software stores data as text (CSV) or proprietary binary blobs (XLSX). CalcTale converts data into a geometric matrix using the Morton (Z-order) Curve.

### IEEE 754 64-Bit Encoding
Each data point is treated as a 64-bit float. To preserve every bit, the system shreds the float across a 4-pixel "Quad-Token" cluster. 
* **Pixel 1-3:** Store the 8 bytes of the double-precision number across RGB channels.
* **Pixel 4:** Acts as a forensic heartbeat, using the Alpha channel to indicate data presence and prevent null-space corruption.

### Spatial Indexing via Morton Curve
By mapping 1D data IDs to 2D coordinates using bit-interleaving, CalcTale ensures that mathematically related datasets are physically adjacent within the image matrix. This spatial coherence significantly improves lossless PNG compression ratios and speeds up forensic auditing.

## Operational Workflow for Physics and Engineering Suites

### Initialization
Users must mount a local project directory using the File System Access API. This establishes a persistent, secure link between the browser's memory and the physical hardware, managed via an IndexedDB handshake.

### Data Ingestion (Baking)
1. **Single Token:** Manual input for individual forensic verification.
2. **Batch Processing:** Ingesting CSV files containing up to 4,000,000 rows. The engine calculates the physics/engineering results and "bakes" them into the MZMO matrix in milliseconds.

### Forensic Batch Auditing
The platform allows for high-frequency bit-drift analysis. By comparing a Baseline MZMO against one or more Comparative MZMOs, the engine identifies variances at the 64-bit level.
* **Match:** Values are identical to the 17th decimal place (highlighted in Blue).
* **Drift:** Any bit-level variance is identified and calculated as a Delta (highlighted in Red/Green).

## Operational Workflow for Statistics Suite

### Initialization
Users must mount a local project directory using the File System Access API. This establishes a persistent, secure link between the browser's memory and the physical hardware. This automates tasks for the user.

### Analytic Models
1. **Linear Regression (OLS):** Isolate continuous variable dependencies by solving the normal equation through Gaussian-Jordan matrix inversion.
2. **Logistic Regression (MLE):** Classification of binary outcomes using Iteratively Reweighted Least Squares (IRLS) to maximize the likelihood of the observed fractal state.

### Structural Integrity & Robustness
The engine performs real-time diagnostic checks to ensure mathematical stability during high-volume stream processing. Users can infinitely conduct data ingestion and regression analysis, though specific test cases can take hours. As it is, an N of 27million+ took approximately 50 seconds. The CSV prior to import was 2.5GBs, composing of 5 MZMO DBs that represented 50MBs per unit for a total of 250MBs. This means the space of this methodology allows you to make data approximately 1000% smaller.
* **Multicollinearity Audit:** Performs Variance Inflation Factor (VIF) diagnostics and Tikhonov Regularization ($\lambda = 10^{-9}$) to maintain matrix stability and prevent inversion failure.
* **Moment Accumulator:** Derives real-time population means ($\mu$) and variances ($\sigma^2$) through out-of-core streaming across high-density Morton-Z fractal chains.
* **Significance Validator:** Converts Wald Z-stats and T-stats into two-tailed probability distributions to verify the forensic integrity of identified data signals.

## Technical Advantages

### Superior Precision
Standard statistical and engineering software often rounds values for display or storage. CalcTale maintains the full 52-bit mantissa of the IEEE 754 standard. In physics applications, this allows for the detection of "Planck-scale" drift that would be swallowed by the rounding errors of traditional tools.

### Industrial Scale and Density
A single 4000 x 4000 MZMO matrix can store 4,000,000 unique rows of data. This is nearly four times the capacity of a standard Excel spreadsheet. Because the data is stored in a lossless PNG, the resulting file is often 90% smaller than an equivalent text-based CSV.

### Computational Speed
Because the ID of a data point is its physical coordinate, the system eliminates the need for "Search" or "Lookup" operations. The Bit-Drift Audit is an O(n) operation performed directly on typed array buffers, allowing it to process millions of comparisons in seconds.

### Forensic Integrity
MZMO matrices are inherently resistant to the "Row-Shift" corruption common in CSV files. Because each token is locked to a specific geometric coordinate, a corruption event in one pixel does not compromise the structural integrity of the surrounding data.

## Deployment

To deploy the platform, the user executes the standalone HTML5 core. All calculations are performed via the client-side CPU/GPU, ensuring total data sovereignty and eliminating the security risks associated with cloud-based engineering platforms.