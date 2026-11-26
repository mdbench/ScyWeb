# SwarmForm

**SwarmForm** is an experimental, proof-of-concept deterministic drone swarm trajectory and convergence model driven by **`2tangno4`** mixing, Morton-Z (`64×64`) spatial indexing, and dual-chain state evolution (`chainAlpha` and `chainBeta`).

> **RESEARCH & SIMULATION PROOF-OF-CONCEPT ONLY — NOT FLIGHT-READY**  
> SwarmForm is an educational and research demonstration proving that deterministic, communication-free swarm formation and target convergence are conceptually possible in RF/EW-contested environments. **It cannot and should not be used for real-world flight tests or operational deployment.**

---

## Overview & Core Concept

Traditional swarm guidance often relies on continuous inter-drone communication, central ground control links, or predictable geometric paths (such as straight-line pursuit or uniform rings/spirals). In contested Electronic Warfare (EW) environments—where radio links are jammed, degraded, or denied—continuous coordination can fail, and simple geometric trajectories can be easier to model or intercept.

SwarmForm explores a different approach:

1. **Zero Inter-Drone Comms During Convergence:** Each drone derives its deterministic slot and trajectory step locally from a shared mission seed/epoch and step/time index, eliminating the need for real-time peer-to-peer RF coordination once launched.
2. **Non-Linear, Seed-Driven Spiral Trajectories:** Instead of a plain linear or uniform spiral, trajectory perturbations and slot assignments are driven by `2tangno4` state mixing and Morton-Z tile coordinates.
3. **Deterministic Spatial Slot Separation:** Bijective odd-strided permutation over a `64×64` (`4,096`-slot) Morton-Z index assigns distinct angular/radial phases to swarm members so nominal paths converge without colliding in ideal space.

---

## How It Works with `2tangno4`

SwarmForm adapts core structural ideas from `2tangno4` into a spatial trajectory generator:

* **Morton-Z (`Z`-Order) Matrix Indexing (`64×64`):** 2D coordinates `(x, y)` are interleaved via bit-spreading (`interleaveBits64` / `deinterleaveBits64`) to map spatial cells onto a `0..4095` Morton-Z curve, preserving local 2D quadtree locality while enabling structured index jumps.
* **Bijective Odd-Strided Slot Permutation:** Each drone `i` maps to a Z-slot and permutes through a deterministic index using an odd stride (`stride_odd`) and offset (`z_offset`) modulo `4096` (`0x0FFF`). Because an odd stride is coprime to `4096`, the mapping is bijective across the tile slot space, keeping assigned slots distinct.
* **Dual-Chain Registers (`chainAlpha`, `chainBeta`) & `bridge` Mixing:** Each step evolves two 32-bit state chains (`chainAlpha` and `chainBeta`) and combines them through a cross-chain `bridge` shift/XOR operation to modulate spiral radius, angular progression, and local offset perturbations deterministically from the mission seed.
* **Target Convergence & Separation Floor:** Each drone computes a converging spiral vector toward the target coordinate while applying radial/phase spacing and a minimum separation floor (`safetyRadius`) in the simulation model.

---

## Why This Is Only a Proof of Concept (EW Resilience vs. Real Flight)

### What the Demo Proves
* A swarm can deterministically compute non-overlapping convergence trajectories **without relying on live RF links** during transit, making pure comms-denial attacks less disruptive to baseline formation geometry.
* Combining seed-driven dual-chain mixing with Morton-Z slot ordering makes trajectories **less trivial to predict** than naive straight-line or uniform-angle approaches.

### Why It Cannot and Should Not Be Used for Real-World Flight
SwarmForm models **idealized kinematics** and omits critical physical, environmental, and safety systems required for real aircraft:

* **No Atmospheric or Wind Compensation:** Wind gusts, crosswinds, turbulence, and air-density shifts push real UAVs off geometric paths and can shrink separation below safe thresholds.
* **No GNSS-Denied / Localization Error Handling:** Real EW environments frequently degrade or spoof satellite navigation; raw position setpoints without fused inertial, visual, or terrain-relative navigation can cause severe drift or flyaways.
* **No Airframe Dynamics or Envelope Limits:** Discrete trajectory steps do not model motor lag, thrust limits, stall speeds, bank/turn-rate constraints, or structural loads.
* **No Closed-Loop Obstacle or Deconfliction Failsafes:** Real airspace contains terrain, obstacles, non-cooperative traffic, battery/link faults, and hardware failures that require deterministic flight-controller failsafes, geofencing, and local collision avoidance—never open-loop spiral math alone.
* **Predictability Is Relative, Not Absolute:** While seed-driven `2tangno4` mixing complicates casual trajectory prediction, any physical aircraft is still bounded by Newtonian physics, observable motion over time, and active sensor/interception defenses.

---

## Integration Blueprint (Simulation / Lab Use Only)

The companion `swarmform.html` visualizer and integration examples illustrate how trajectory setpoints can be structured for **software simulation (such as SITL / ROS 2 / MAVLink offboard)**—for example, computing local `NED` (`SET_POSITION_TARGET_LOCAL_NED`) position/velocity targets at a fixed loop rate while keeping low-level stabilization and geofencing inside the flight controller.

Any testing should remain strictly confined to **isolated simulation environments** (such as SITL) and never be deployed on live aircraft in real-world or operational environments.

---

## License & Disclaimer

Provided for educational, research, and simulation experimentation only. No warranty of safety, fitness for flight, or operational security is provided.