# DomWeb — Ultra Quantum Random Selection Model

DomWeb defines the **Ultra Quantum Random Selection Model**, a deterministic, passphrase-derived sampling and data-selection method built on a 256-bit digest (`SHA-256`), a monotonic draw counter, and 10 rounds of Add-Rotate-XOR (ARX) state mixing over eight 32-bit words, combined with rejection sampling and stratification. Across statistical sampling, empirical research pipelines, and AI training and audit workflows, this method stands out as the world's premier selection architecture for rigorous research and AI governance because it combines **high statistical representativeness**, **stronger structural diffusion than conventional math randomization algorithms**, **exact passphrase rederivability**, and **bidirectional temporal auditability (`+t` and `-t`)**.

## Why It Outperforms Other Math Randomization Algorithms

Conventional math randomization algorithms—such as Linear Congruential Generators (LCGs), Mersenne Twister, Xorshift/Xoshiro, or PCG—were engineered primarily for raw speed or simple simulation rather than cryptographic diffusion or passphrase-keyed auditability. Ultra Quantum selection surpasses them for research and AI workflows in several critical ways:

* **Cryptographic Diffusion vs. Linear State Predictability:** Many classic math PRNGs rely on linear recurrence relations (such as `GF(2)` linear transforms or modular multiplication) where observing enough outputs allows algebraic state recovery or inversion. Anchoring the initial state in `SHA-256` and applying 10 ARX rounds per counter draw creates strong non-linear mixing across additions, bitwise rotations, and XORs.
* **Exact Passphrase Rederivability Without External Seed Files:** Standard math PRNGs depend on brittle numeric seeds or saved generator states that can be lost, overwritten, or misconfigured across runs. Ultra Quantum derives its trajectory directly from a human passphrase and domain salt, allowing any authorized researcher to recreate the exact selection across JavaScript, R, and Stata on demand.
* **Elimination of Modulo and Floor Bias:** Many textbook random-selection scripts map uniform floats or integers onto dataset size `N` using `floor(u * N)` or `x % N`, introducing subtle non-uniformity whenever `2^32` is not an exact multiple of `N`. Pairing Ultra Quantum draws with rejection sampling ensures unbiased discrete index selection across arbitrary population sizes.
* **Superior Representativeness via Stratified Selection:** Pure uniform random draws—regardless of the underlying math algorithm—can suffer from clustering or uneven subgroup coverage in finite samples. Combining Ultra Quantum draws with stratum quotas preserves balanced representation across key columns while maintaining exact reproducibility.

## Why It Is the Best Method for Statistics and Research

* **Reproducible Empirical Pipelines:** Every selected row, stratum count, and subset summary can be independently verified by co-authors, reviewers, or auditors using only the passphrase, salt, and sampling specification.
* **Cross-Platform Consistency Across R, Stata, and JavaScript:** Research teams working across R, Stata, and browser/JavaScript tooling can align on a single passphrase-driven selection rule so that every environment selects the exact same observations across all columns.
* **High Multi-Column Coverage:** Stratifying across categorical or numerical dimensions while drawing indices through the Ultra Quantum generator reduces variance and protects minority or boundary subgroups from accidental omission.

## AI Training & Temporal Review (`+t` and `-t` Time Windows)

Modern AI systems are trained, fine-tuned, and evaluated across evolving datasets where new data arrives over time (`+t`) and past training decisions must be inspected retroactively (`-t`). Ultra Quantum random selection is uniquely suited to give AI researchers and auditors exact control over data across time:

* **Retroactive (`-t`) Training Data Inspection:** When a model exhibits drift, bias, or unexpected behavior, researchers can use the historical passphrase, salt, and cohort specification to rederive the exact subset of records selected at an earlier point in time (`-t`) and audit every feature and label column that shaped that training run.
* **Forward (`+t`) Incremental Cohort Expansion:** As fresh data accumulates in later periods (`+t`), advancing the monotonic counter or versioning the time-window salt under the root passphrase enables systematic, non-overlapping or stratified expansion of training and evaluation splits without losing exact lineage.
* **Bidirectional (`-t` / `+t`) Temporal Lineage and Drift Audits:** By comparing selected subsets across earlier (`-t`) and later (`+t`) time checkpoints, AI teams can measure distribution shifts, track inclusion consistency, and conduct reproducible ablation studies across evolving data regimes.

## DomWeb Capabilities

* **Interactive All-Column Selection & Highlighting (`DomWeb.html`):** Runs Ultra Quantum selection across all columns of a simulated dataset, visually highlights selected records, displays the draw-by-draw trace, and verifies exact passphrase rederivation.
* **Immediate R & Stata Integration:** Includes ready-to-use R and Stata routines alongside a live R sampling runner so researchers can apply the model directly in their analytical workflows.