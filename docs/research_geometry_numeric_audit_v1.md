# Numerical geometry audit: adjacent cells falsely treated as overlap

The same-grade 10% near-tissue exclusion for host `3901caec5d914bf20a44f176469b0294`, donor `14cff64d674f558dc47ee5e817b7f671`, seed `20261021` was caused by **floating-point phantom overlap**, rather than infeasibility of that full donor fragment. This diagnosis uses two hash-verified training coordinate CSVs and the sealed cached foreground mask. It reads no WSI, saved feature matrix, model or held-out input and submits no job.

## Exact arithmetic

The proposed anchor x was `1006.4084085185101` µm. Storing the translation relative to donor minimum x `4249.279947078154` and reconstructing the anchor produced `1006.40840851851` µm: a difference of **−1.1368683772161603e−13 µm**.

For donor tile 218 (`x38-y25`), the translated position at the host grid's x=9 boundary changed by this amount. Adjacent native host tiles 167 (`x8-y42`) and 172 (`x8-y43`) end at x=`1006.4084085185101`. Strict floating rectangle inequalities therefore reported a positive intersection width of `1.1368683772161603e−13` µm. Tile 172 additionally had a floating y-intersection of `9.094947017729282e−13` µm.

The observed RGB raster rectangle remained exactly `[129,603]` to `[144,619]`; its foreground count remained **zero**. All 52 original/proposed raster rectangles are identical under this roundtrip. This specific defect is the host-footprint collision test; it is not evidence that the foreground threshold or 224 µm proximity requirement should be relaxed. The audit does not attribute the other 326 exclusions to the same cause.

A minimal arithmetic counterexample is:

```python
step = 111.82315650205668
host_right = 894.5852520164534 + step
anchor = 1006.4084085185101
donor_minimum = 4249.279947078154
roundtrip = donor_minimum + (anchor - donor_minimum)
assert anchor == host_right
assert roundtrip < host_right
assert round(anchor / step) == round(roundtrip / step) == 9
```

## Smallest contract correction

For coordinates already validated against the declared common tile grid, with positive tile size no larger than its grid step, footprints overlap **exactly when they own the same integer grid cell**. `_valid_position` now uses this ownership rule for host collisions. It reuses the existing grid-alignment tolerance and rejects invalid sizes, unaligned coordinates and duplicate placement cells. There is no physical-overlap epsilon and no new geometric threshold.

Coordinates are not snapped or rewritten. RGB rasterization, physical bounds and the proximity check remain unchanged. The correction changes validation only, leaving result arrays, metadata, fingerprints and JSON construction unchanged. Off-grid placements are rejected rather than rounded into apparently safe positions.

Tests cover the actual numeric counterexample with a software fixture, touching adjacency, occupied cells, off-grid overlap, duplicate cells, invalid footprints and an unaligned host. The existing engine/acceptance suite passes **31 tests**, including exact legacy/oracle and complete fixture workflows.

## Provenance

| Input | Host `3901caec…` SHA-256 | Donor `14cff64d…` SHA-256 |
|---|---|---|
| `tiles.csv` | `c1c57b8737bcc22c8b631134d08c5f66517e8c713506044d053c5641736cbedc` | `c889bc001cc3552f4ede34f583d229f77434bb6c8a1e19f69456ce4b8619ec2c` |
| Embedding `completion.json` | `eff8677f719ddca3c3de5fc5d8dcef11b89bbc65ded2c94d75fc3fdd1a0c2e39` | `6a694eb1831503b6c039fe9477ddec02f0ae7519d60ca00d89459fe189e1e678` |

Both coordinate/metadata files match the completion receipts, and both completion SHA values match the prior verified embedding ledger. [The machine audit](../reports/research_geometry_numeric_audit_v1.json) contains full paths, metadata hashes, the original geometry-checkpoint hash and the exact before/after arithmetic.

The original job `23069070`, its 1,017 eligible cases, all **327 historical exclusions**, and all original staged source snapshots/configs/results remain unchanged. This technical fix does not retroactively admit the diagnosed case into the completed study. The next paired detector analysis must retain its predeclared old eligibility, rather than selecting additional cases after seeing any outcomes.
