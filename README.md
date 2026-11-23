# EC Cost Simulator

Evaluates the **repair cost of erasure codes** in distributed storage. For every code it
enumerates every loss pattern exhaustively and measures what a repair has to read, then plots the
distributions. Written to compare the hybrid **Hitchhiker-LRC** against the alternatives from the
literature, on the target infrastructure of a real deployment.

## Codes

| Class | Code | Substripes | Parameters | Reference |
| --- | --- | --- | --- | --- |
| `RS` | Reed-Solomon | 1 | `s`, `r` | [1] |
| `LRC` | Uniform Cauchy LRC | 1 | `s`, `r`, `l` | [2] |
| `HH` | Hitchhiker-XOR | 2 | `s`, `r` | [3] |
| `HHLRC` | Hitchhiker-LRC | 2 | `s`, `r`, `l` | — |
| `DESIGN2` | Piggybacking Design 2 | `2r - 3` | `s`, `r` | [4] |
| `CLAY` | Clay, an MSR code | `q^t` | `s`, `r`, `d` | [5] |

`s` data fragments, `r` global parities, `l` local parities, `d` helper fragments. Local parities
are added on top of the MDS core rather than taken from it, so `n = s + r + l` and the storage
ratio `n / s` prices locality instead of hiding it in a smaller `s`.

## Measures

- **symbols read**, `symbol_cost`, the substripes a repair reads, normalized by `s * alpha`
- **sequential reads**, `sequential_read_cost`, the read operations: contiguous substripes of one
  fragment count as one, a gap starts another, normalized by `s`

A code that cannot repair a pattern economically falls back on a full Reed-Solomon read, which caps
every cost at `s * alpha`. A pattern that cannot be repaired at all returns `None`.

## Usage

```bash
./run.sh     # build the figures into graphs/, for (s, r) = (17, 10), l = 1..3, 1 to 3 losses
./test.sh    # run the test suite
```

Both source `setup.sh`, which creates the virtual environment and installs the package.

## References

1. I. S. Reed, G. Solomon. *Polynomial Codes Over Certain Finite Fields*. Journal of the SIAM 8(2), 1960. [doi:10.1137/0108018](https://doi.org/10.1137/0108018)
2. S. Kadekodi, S. Silas, D. Clausen, A. Merchant. *Practical Design Considerations for Wide Locally Recoverable Codes (LRCs)*. USENIX FAST 2023; ACM Transactions on Storage 19(4), 2023. [doi:10.1145/3626198](https://doi.org/10.1145/3626198)
3. K. V. Rashmi, N. B. Shah, D. Gu, H. Kuang, D. Borthakur, K. Ramchandran. *A "Hitchhiker's" Guide to Fast and Efficient Data Reconstruction in Erasure-coded Data Centers*. ACM SIGCOMM 2014. [doi:10.1145/2619239.2626325](https://doi.org/10.1145/2619239.2626325)
4. K. V. Rashmi, N. B. Shah, K. Ramchandran. *A Piggybacking Design Framework for Read- and Download-Efficient Distributed Storage Codes*. IEEE Transactions on Information Theory 63(9), 2017. [doi:10.1109/TIT.2017.2715043](https://doi.org/10.1109/TIT.2017.2715043)
5. M. Vajha et al. *Clay Codes: Moulding MDS Codes to Yield an MSR Code*. USENIX FAST 2018. [usenix.org](https://www.usenix.org/conference/fast18/presentation/vajha)
