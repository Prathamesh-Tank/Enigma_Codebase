<p align="center">
  <h1 align="center"> ChampSim </h1>
  <p> ChampSim is a trace-based simulator for a microarchitecture study. You can find more information about ChampSim here (https://github.com/ChampSim/ChampSim)     <p>
  <p> This repository contains implementation for state-of-the-art randomized caches i.e. CEASER, CEASER-S, and ScatterCache. It also contain our DAMARU attacker code. You can find more information about DAMARU in the paper.
</p>

# Requirements 

This setup is tested with GCC 7.5 and Ubuntu 18.04. To install GCC 7.5 in Ubuntu 20.04 :-

```
sudo apt install build-essential
sudo apt install g++-7
```

# Compile

   
```
Usage:
./build_champsim.sh [BRANCH] [L1D_Pref] [L2C_Pref] [LLC_Pref] [LLC_Replacement] [NUM_CORE] [IS_HUGE_PAGE] [IS_DIVIDED_QUEQUES] [CEASER_S_LLC] [Partition] [Pipelined Encryption Engine] [CEASER LATENCY] [Remapping] [Remap_on_eviction] [LLC_SLICE]

${BRANCH}                         : Branch Predictor
${L1_Pref} {L2C_Pref} {LLC_Pref}  : Prefetcher at L1D,L2C,and LLC respectively
${LLC_Replacement}                : Replacement policy at LLC 
${NUM_CORE}                       : Number of cores
${IS_HUGE_PAGE}                   : Enabling page size of 2 MB 
${IS_DIVIDED_QUEQUES}             : Enabling SMT
${CEASER_S_LLC}                   : Enabling CEASER-S 
${Partition}                      : Number of partition in CEASER-S
${Pipelined_Encryption Engine]    : Nature of the encryption engine {pipelined or non-pipelined}
${CEASER LATENCY}                 : Encryption engine Latency 
${Remapping}                      : Enabling remapping in randomized caches
${Remap_on_eviction}              : Remapping based on the number of LLC evictions
${LLC SLICE}                      : Number of 2 MB LLC Slice

```
Use build_champsim.sh script with proper input arguments to compile different randomized caches. The build_champsim.sh contains knob named "CEASER-S" and "partitions" for building different randomized caches :-

|Knob|CEASER-S|Partitions| Compile
|----------|------------|------------|------------|
|Baseline|0|1|./build_champsim.sh bimodal no no no srrip 1 0 -1  0 1 1 3 0 1 1 |
|[CEASER](http://memlab.ece.gatech.edu/papers/MICRO_2018_2.pdf)|1|1| ./build_champsim.sh bimodal no no no srrip 1 0 -1 1 1 1 3 1 0 1 |
|[CEASER-S](https://memlab.ece.gatech.edu/papers/ISCA_2019_1.pdf)|1|2| ./build_champsim.sh bimodal no no no srrip 1 0 -1 1 2 1 3 1 0 1 |
|[ScatterCache](https://www.usenix.org/system/files/sec19-werner.pdf)|1|16| ./build_champsim.sh bimodal no no no srrip 1 0 -1  1 16 1 3 1 0 1 |

For more details please refer to build_champsim.sh

# Modes

`build_champsim.sh` now selects the LLC cache mode at compile time based on `LLC_Replacement`.

The supported comparison modes are:

- `enigma`: Mirage-style secure tag store + SSL + local SRRIP + deferred SoS
- `mirage`: Mirage-style secure tag store + global random data-store placement/replacement
- `srrip`: conventional non-randomized set-associative SRRIP without the Mirage/Enigma pointer-based tag store

The build script writes these mode macros into `inc/cache_mode.h` automatically, so you do not need to edit `inc/cache.h` by hand.

# Enigma

Enigma keeps the Mirage-style secure tag-store foundation and uses:

- SSL-guided data-store set selection
- local SRRIP replacement inside the SSL-selected data-store set
- deferred SoS servicing on later misses

The current Enigma implementation keeps:

- two randomized skews in the tag store
- over-provisioned tag entries
- power-of-two-choices / load-aware skew selection
- forward and reverse tag-data pointers

Build Enigma with:

```bash
./build_champsim.sh bimodal no no no enigma 1 0 -1 0 1 1 3 0 1 1
```

This produces:

```bash
bin/bimodal-no-no-no-enigma-0-1-1-3-0-1-1core-1core_llc
```

Run Enigma on the DPC3 `mcf` trace with:

```bash
./run_champsim.sh bimodal-no-no-no-enigma-0-1-1-3-0-1-1core-1core_llc 1 1 ../dpc3_traces 605.mcf_s-1554B.champsimtrace.xz
```

Important Enigma knobs in `inc/cache.h`:

- `ENIGMA_SOS_THRESHOLD`: current value is `2`

The compile-time mode bits are generated in `inc/cache_mode.h`:

- `MIRAGE`
- `ENIGMA_ENABLE_SSL_SRRIP`
- `ENIGMA_ENABLE_SOS_SUPERVISOR`
- `ENIGMA_USE_GLOBAL_RANDOM_DATA`
- `LLC_SECURITY_MODE`

Useful comparison points:

- `mirage` for Mirage-style comparison
- `srrip` for conventional non-randomized set-associative SRRIP
- `enigma` for SSL + local SRRIP + deferred SoS

Build Mirage with:

```bash
./build_champsim.sh bimodal no no no mirage 1 0 -1 0 1 1 3 0 1 1
```

Build plain non-randomized SRRIP with:

```bash
./build_champsim.sh bimodal no no no srrip 1 0 -1 0 1 1 3 0 1 1
```

# Run simulation

Execute `run_champsim.sh` with proper input arguments. <br>

```
Usage: ./run_champsim.sh [BINARY] [N_WARM] [N_SIM] [TRACE] [OPTION]
$ /run_champsim.sh hashed_perceptron-no-no-no-ship-1-1-1-3-1-1-1core-1core_llc 1 1 605.mcf_s-1554B.champsimtrace.xz

${BINARY}: ChampSim binary compiled by "build_champsim.sh" (bimodal-no-no-no-ship-1-1-1-3-1-1-1core-1core_llc)
${N_WARM}: number of instructions for warmup (1 million)
${N_SIM}:  number of instructinos for detailed simulation (1 million)
${TRACE}: trace name (605.mcf_s-1554B.champsimtrace.xz)
${OPTION}: Provide -cvp_trace for running CVP traces.
```

# Reproducing Enigma Results

To make single-core Enigma-style runs reproducible without editing personal paths, use:

```bash
./recreate_enigma_results.sh ../dpc3_traces 200 200 enigma reproduced_results_enigma_200M_200M 4
```

Arguments:

- `TRACE_DIR`: directory containing `.champsimtrace.xz` and/or `.trace.gz` traces
- `N_WARM`: warmup length in millions of instructions
- `N_SIM`: simulation length in millions of instructions
- `LLC_MODE`: `enigma`, `mirage`, or `srrip`
- `RESULTS_SUBDIR`: output folder created under `performance-analysis/enigma`
- `MAX_JOBS`: number of parallel runs

The script:

- builds the requested LLC mode using `build_champsim.sh`
- discovers traces from the provided trace directory
- runs each trace through `run_champsim.sh`
- collects outputs into the chosen results folder

# Enigma Artifact-Style Workflow

If you want a paper-style reproduction flow similar to the Maya artifact, use the following. This flow builds and compares:

- `enigma`: Mirage tag store + SSL + local SRRIP + deferred SoS
- `enigma+maya`: Maya-derived cache with Enigma-style SSL/local-SRRIP/SoS behavior
- `mirage`: Mirage secure tag store + global random data-store eviction
- `srrip`: conventional non-randomized set-associative SRRIP
- `maya`: original Maya artifact binaries

1. Clone the repository:

```bash
git clone https://github.com/AnubhavBhatla/maya-cache
```

2. Enter the performance-analysis directory:

```bash
cd maya-cache/performance-analysis
```

3. Download the required traces:

- Download the GAP traces zip file into `performance-analysis/traces/`
- Run:

```bash
./traces.sh
```

This downloads the required SPEC traces and extracts the GAP traces into the correct `traces/spec` and `traces/gap` directories.

4. Generate the required Enigma comparison binaries:

```bash
./compile_enigma.sh
```

This creates the following binaries:

- `srrip_1core_2MB`
- `mirage_1core_2MB`
- `enigma_1core_2MB`
- `enigma_1core_16MB_8slices`
- `mirage_1core_16MB_8slices`
- `srrip_1core_16MB_8slices`
- `enigma_8core_16MB`
- `mirage_8core_16MB`
- `srrip_8core_16MB`
- `maya_1core_12MB_3way_8slices`
- `maya_8core_12MB_3way`
- `enigma_maya_1core_12MB_3way_8slices`
- `enigma_maya_8core_12MB_3way`

Locations:

- `performance-analysis/enigma/bin/` for Enigma, Mirage, and SRRIP
- `performance-analysis/maya/bin/` for Maya
- `performance-analysis/enigma+maya/bin/` for Enigma+Maya

Note: the comparison CSV keeps the configuration label for each mode because Maya and Enigma+Maya remain in Maya-derived `12MB 3-way` configurations, while Enigma, Mirage, and SRRIP use the Enigma comparison setup.

5. Run the performance simulations:

```bash
./run_enigma.sh
```

This launches the full Maya-style Enigma artifact run matrix:

- single-core 2MB deadblock runs for `srrip`, `mirage`, and `enigma`
- single-core SPEC and GAP runs for `enigma`, `mirage`, `srrip`, `maya`, and `enigma+maya`
- homogeneous 8-core SPEC and GAP runs for `enigma`, `mirage`, `srrip`, `maya`, and `enigma+maya`

Outputs are written under:

- `performance-analysis/enigma/results/`
- `performance-analysis/maya/results/`
- `performance-analysis/enigma+maya/results/`

6. Collect the comparison CSVs and plots:

```bash
./plot_enigma.sh 0
```

This produces:

- `performance-analysis/enigma/compare_outputs/singlecore_trace_summary.csv`
- `performance-analysis/enigma/compare_outputs/singlecore_benchmark_summary.csv`
- `performance-analysis/enigma/compare_outputs/singlecore_suite_summary.csv`
- `performance-analysis/enigma/compare_outputs/deadblock_trace_summary.csv`
- `performance-analysis/enigma/compare_outputs/deadblock_benchmark_summary.csv`
- `performance-analysis/enigma/compare_outputs/multicore_trace_summary.csv`
- `performance-analysis/enigma/compare_outputs/multicore_benchmark_summary.csv`
- `performance-analysis/enigma/compare_outputs/multicore_suite_summary.csv`
- `performance-analysis/enigma/compare_outputs/FigE1_singlecore_ipc_norm_vs_srrip.pdf`
- `performance-analysis/enigma/compare_outputs/FigE2_singlecore_llc_hit_rate.pdf`
- `performance-analysis/enigma/compare_outputs/FigE3_singlecore_mpki.pdf`
- `performance-analysis/enigma/compare_outputs/FigE4_deadblocks.pdf`
- `performance-analysis/enigma/compare_outputs/FigE5_multicore_weighted_speedup_norm_vs_srrip.pdf`
- `performance-analysis/enigma/compare_outputs/FigE6_multicore_weighted_speedup_by_benchmark.pdf`

The CSV files keep the fine-grain per-trace, per-benchmark, and per-suite fields needed for custom figures, including IPC, LLC hit and miss statistics, MPKI, miss latency, data-store balancing statistics, RRPV statistics, tag-store occupancy statistics, SoS activity, deadblock percentage, raw multicore IPC, and weighted speedup.

7. To parse packaged results instead of freshly generated runs, use:

```bash
./plot_enigma.sh 1
```

This reads:

- `performance-analysis/enigma/alltraces_enigma/` for packaged Enigma, Mirage, and SRRIP runs
- `performance-analysis/maya/original_results/` for packaged Maya runs when present

Packaged mode currently supports the packaged single-core result sets. The full deadblock and homogeneous 8-core comparison is produced from fresh runs via `./run_enigma.sh`.

8. For targeted or custom Enigma runs, use:

```bash
cd enigma
./recreate_enigma_results.sh ../traces/spec 200 200 enigma reproduced_results_enigma_spec 4
```

or for GAP:

```bash
./recreate_enigma_results.sh ../traces/gap 200 200 enigma reproduced_results_enigma_gap 4
```

9. Enter the security-analysis directory:

```bash
cd ../security-analysis
```

10. Generate the required security binaries:

```bash
make
```

11. Run the security simulations:

```bash
./run_compare_all.sh --billion-tries 1 --seed 1 --extra-ways 1,2,3,4,5,6
```

12. Inspect the security comparison outputs:

- raw outputs are written under `security-analysis/results/`
- CSV summaries are emitted by the comparison runner for plotting and analysis

# Replicating the results from the paper

The traces used in evalution can be generated by using pin tool. For each trace, the results are captured for 1M instructions after a warmup of 1M instructions. 
