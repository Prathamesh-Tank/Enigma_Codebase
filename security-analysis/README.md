# security-analysis

Acknowledgement: This code has been adapted from the code released by the authors of MIRAGE
https://github.com/gururaj-s/mirage

Security-analysis models in this folder:

- `src/security_mirage.cpp`: Mirage tag-store model with global random data-store eviction.
- `src/security_maya.cpp`: Maya bins-and-balls model.
- `src/bucketsNballs_SSL_LocalRandom_NBn.cpp`: Mirage-tag-store variant with round-robin SSL and local random data-store victim selection.

Build outputs:

- `bin/mirage.o`
- `bin/maya6Ways.o`
- `bin/mirage_ssl_local_random.o`

Windows-native comparison runner:

```powershell
cd security-analysis
.\run_compare_all.ps1 -BillionTries 1 -Seed 1 -ExtraWays 1,2,3,4,5,6
```

WSL / bash comparison runner:

```bash
cd security-analysis
./run_compare_all.sh --billion-tries 1 --seed 1 --extra-ways 1,2,3,4,5,6
```

Quick smoke test:

```powershell
cd security-analysis
.\run_compare_all.ps1 -SmokeTest -BillionTries 1 -Seed 1 -ExtraWays 6
```

WSL smoke test:

```bash
cd security-analysis
./run_compare_all.sh --smoke-test --billion-tries 1 --seed 1 --extra-ways 6
```

Outputs are written under:

- full run: `results/comparison_1Bn/`
- smoke run: `results/comparison_smoke/`

Each output directory contains:

- `raw_results/*.out`
- `security_compare_summary.csv`
- `security_compare_bucket_prob.csv`
- `security_compare_dest_bucket.csv`
