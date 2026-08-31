#!/bin/bash

# ==========================================================
# Script: run_8core.sh
# Purpose: Run ChampSim for 8-core with 8 traces
# ==========================================================

if [ "$#" -lt 13 ]; then
    echo "Usage: ./run_8core.sh [BINARY] [N_WARM] [N_SIM] [TRACE_DIR] [TRACE1] [TRACE2] [TRACE3] [TRACE4] [TRACE5] [TRACE6] [TRACE7] [TRACE8] [OPTION]"
    exit 1
fi

BINARY=${1}
N_WARM=${2}
N_SIM=${3}
TRACE_DIR=${4}
TRACE1=${5}
TRACE2=${6}
TRACE3=${7}
TRACE4=${8}
TRACE5=${9}
TRACE6=${10}
TRACE7=${11}
TRACE8=${12}
OPTION=${13}

# Sanity check
if [ ! -d "$TRACE_DIR" ]; then
    echo "[ERROR] Trace directory not found: $TRACE_DIR"
    exit 1
fi

if [ ! -f "bin/$BINARY" ]; then
    echo "[ERROR] ChampSim binary not found: bin/$BINARY"
    exit 1
fi

# Check that each trace exists
for TRACE in "$TRACE1" "$TRACE2" "$TRACE3" "$TRACE4" "$TRACE5" "$TRACE6" "$TRACE7" "$TRACE8"; do
    if [ ! -f "$TRACE_DIR/$TRACE" ]; then
        echo "[ERROR] Trace file not found: $TRACE_DIR/$TRACE"
        exit 1
    fi
done

# Make folder based on number of simulation instructions (in millions)
RESULTS_DIR="results_${N_SIM}M"
mkdir -p "$RESULTS_DIR"

# Run ChampSim and dump output to mix.txt inside that folder
./bin/$BINARY \
    -warmup_instructions ${N_WARM}000000 \
    -simulation_instructions ${N_SIM}000000 \
    ${OPTION} \
    -traces \
    "$TRACE_DIR/$TRACE1" \
    "$TRACE_DIR/$TRACE2" \
    "$TRACE_DIR/$TRACE3" \
    "$TRACE_DIR/$TRACE4" \
    "$TRACE_DIR/$TRACE5" \
    "$TRACE_DIR/$TRACE6" \
    "$TRACE_DIR/$TRACE7" \
    "$TRACE_DIR/$TRACE8" \
    > "${RESULTS_DIR}/mix.txt" 2>&1

