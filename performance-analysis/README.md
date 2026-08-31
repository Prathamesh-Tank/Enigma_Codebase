# Performance Analysis Artifacts

This repository now contains two artifact-style performance flows:

- `Maya`: the original Maya artifact workflow
- `Enigma`: a comparison workflow for `enigma`, `enigma+maya`, `maya`, `mirage`, and `srrip`

## Maya Artifact

Use the original Maya scripts when you want to reproduce the Maya paper flow exactly:

```bash
./compile.sh
./run.sh
./plot.sh 0
```

These scripts use the original Maya and Mirage result layout and figure flow.

## Enigma Artifact

Use the Enigma scripts when you want a Maya-style artifact flow for comparing:

- `enigma`: Mirage-style secure tag store + SSL + local SRRIP + deferred SoS
- `enigma+maya`: Maya-derived cache organization with Enigma-style SSL/local-SRRIP/SoS behavior
- `mirage`: Mirage-style secure tag store + global random data-store replacement
- `srrip`: non-randomized set-associative SRRIP baseline
- `maya`: original Maya cache design

### Reproduction Steps

1. Clone the repository:

```bash
git clone https://github.com/AnubhavBhatla/maya-cache
```

2. Enter the performance-analysis directory:

```bash
cd maya-cache/performance-analysis
```

3. Download the traces:

- Download the GAP traces zip into `performance-analysis/traces/`
- Run:

```bash
./traces.sh
```

This populates:

- `performance-analysis/traces/spec`
- `performance-analysis/traces/gap`

4. Build the Enigma comparison binaries:

```bash
./compile_enigma.sh
```

This builds:

- deadblock binaries:
  - `enigma/bin/srrip_1core_2MB`
  - `enigma/bin/mirage_1core_2MB`
  - `enigma/bin/enigma_1core_2MB`
- single-core binaries:
  - `enigma/bin/srrip_1core_16MB_8slices`
  - `enigma/bin/mirage_1core_16MB_8slices`
  - `enigma/bin/enigma_1core_16MB_8slices`
  - `maya/bin/maya_1core_12MB_3way_8slices`
  - `enigma+maya/bin/enigma_maya_1core_12MB_3way_8slices`
- homogeneous 8-core binaries:
  - `enigma/bin/srrip_8core_16MB`
  - `enigma/bin/mirage_8core_16MB`
  - `enigma/bin/enigma_8core_16MB`
  - `maya/bin/maya_8core_12MB_3way`
  - `enigma+maya/bin/enigma_maya_8core_12MB_3way`

5. Run the Enigma comparison experiments:

```bash
./run_enigma.sh
```

This launches:

- deadblock-style single-core `2MB` runs for `srrip`, `mirage`, and `enigma`
- single-core SPEC and GAP runs for `enigma`, `mirage`, `srrip`, `maya`, and `enigma+maya`
- homogeneous 8-core SPEC and GAP runs for `enigma`, `mirage`, `srrip`, `maya`, and `enigma+maya`

Results are written under:

- `performance-analysis/enigma/results/`
- `performance-analysis/maya/results/`
- `performance-analysis/enigma+maya/results/`

6. Generate Enigma comparison CSVs and plots:

```bash
./plot_enigma.sh 0
```

This writes outputs under:

- `performance-analysis/enigma/compare_outputs/`

Key CSV outputs:

- `singlecore_trace_summary.csv`
- `singlecore_benchmark_summary.csv`
- `singlecore_suite_summary.csv`
- `deadblock_trace_summary.csv`
- `deadblock_benchmark_summary.csv`
- `multicore_trace_summary.csv`
- `multicore_benchmark_summary.csv`
- `multicore_suite_summary.csv`

Key plot outputs:

- `FigE1_singlecore_ipc_norm_vs_srrip.pdf`
- `FigE2_singlecore_llc_hit_rate.pdf`
- `FigE3_singlecore_mpki.pdf`
- `FigE4_deadblocks.pdf`
- `FigE5_multicore_weighted_speedup_norm_vs_srrip.pdf`
- `FigE6_multicore_weighted_speedup_by_benchmark.pdf`

### Packaged Results Mode

If you want to parse packaged results instead of fresh runs, use:

```bash
./plot_enigma.sh 1
```

This reads:

- `performance-analysis/enigma/alltraces_enigma/`
- `performance-analysis/maya/original_results/`

Packaged mode is strongest for the packaged single-core comparison inputs. The full deadblock and homogeneous 8-core comparison is intended to come from fresh runs.

### Important Comparison Note

The Enigma comparison CSVs keep the configuration label for each mode because the capacities are not all identical:

- `enigma`, `mirage`, and `srrip` use the Enigma comparison setup
- `maya` remains in its original Maya artifact configuration
- `enigma+maya` remains in its Maya-derived artifact configuration

That way, downstream analysis and plots can remain honest about which configuration produced each result.

## Enigma Design Intent

The Enigma flow models:

- Mirage-style secure tag-store foundation
- SSL-guided data-store set selection
- local SRRIP inside the SSL-selected data-store set
- deferred SoS supervision

This is meant to model:

`Enigma = Mirage tag-store security foundation + SSL/SRRIP common path + deferred SoS security supervisor`

It is not meant to model Enigma as just “SRRIP instead of random replacement.”
