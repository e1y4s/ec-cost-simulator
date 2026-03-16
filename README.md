# EC Cost Simulator

EC Cost Simulator is a Python simulator designed to evaluate the **reconstruction cost of erasure coding schemes** in distributed storage systems.
It was developed as part of research on optimizing repair costs for **Reed–Solomon–based storage systems**, and was used to evaluate the hybrid **Hitchhiker–LRC** scheme.

## Features

- Simulation of erasure coding schemes:
  - Reed–Solomon (RS)
  - Hitchhiker (HH)
  - Uniform Cauchy LRC (LRC)
  - Hybrid Hitchhiker–LRC (HHLRC)
- Exhaustive evaluation of failure combinations
- Computation of normalized reconstruction cost
- Generation of repair cost distribution histograms

## Reconstruction Cost

The reconstruction cost corresponds to the number of fragments read during repair and is normalized relative to Reed–Solomon:

```
c_normalized = (fragments_read / s) × 100
```

where `s` is the number of data fragments

## Usage

```bash
./run.sh
```

The simulator evaluates repair costs for different coding schemes and produces histogram visualizations of the results.
