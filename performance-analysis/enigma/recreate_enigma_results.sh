#!/bin/bash

set -euo pipefail

if [ "$#" -lt 1 ] || [ "$#" -gt 6 ]; then
    echo "Usage: ./recreate_enigma_results.sh [TRACE_DIR] [N_WARM] [N_SIM] [LLC_MODE] [RESULTS_SUBDIR] [MAX_JOBS]"
    echo ""
    echo "  TRACE_DIR       Directory containing ChampSim traces"
    echo "  N_WARM          Warmup instructions in millions (default: 200)"
    echo "  N_SIM           Simulation instructions in millions (default: 200)"
    echo "  LLC_MODE        enigma | mirage | srrip (default: enigma)"
    echo "  RESULTS_SUBDIR  Output folder under performance-analysis/enigma (default: reproduced_results_<mode>_<warm>M_<sim>M)"
    echo "  MAX_JOBS        Number of parallel runs (default: 1)"
    exit 1
fi

TRACE_DIR=$1
N_WARM=${2:-200}
N_SIM=${3:-200}
LLC_MODE=${4:-enigma}
RESULTS_SUBDIR=${5:-reproduced_results_${LLC_MODE}_${N_WARM}M_${N_SIM}M}
MAX_JOBS=${6:-1}

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR"

case "$LLC_MODE" in
    enigma|mirage|srrip)
        ;;
    *)
        echo "[ERROR] LLC_MODE must be one of: enigma, mirage, srrip"
        exit 1
        ;;
esac

if [ ! -d "$TRACE_DIR" ]; then
    echo "[ERROR] Cannot find trace directory: $TRACE_DIR"
    exit 1
fi

if ! [[ "$N_WARM" =~ ^[0-9]+$ ]]; then
    echo "[ERROR] N_WARM must be a non-negative integer"
    exit 1
fi

if ! [[ "$N_SIM" =~ ^[0-9]+$ ]]; then
    echo "[ERROR] N_SIM must be a non-negative integer"
    exit 1
fi

if ! [[ "$MAX_JOBS" =~ ^[0-9]+$ ]] || [ "$MAX_JOBS" -lt 1 ]; then
    echo "[ERROR] MAX_JOBS must be an integer >= 1"
    exit 1
fi

BUILD_CMD=(./build_champsim.sh bimodal no no no "$LLC_MODE" 1 0 -1 0 1 1 3 0 1 1)
echo "[INFO] Building ${LLC_MODE} binary..."
"${BUILD_CMD[@]}"

BINARY="bimodal-no-no-no-${LLC_MODE}-0-1-1-3-0-1-1core-1core_llc"
if [ ! -f "bin/${BINARY}" ]; then
    echo "[ERROR] Expected binary not found after build: bin/${BINARY}"
    exit 1
fi

RESULTS_DIR="${SCRIPT_DIR}/${RESULTS_SUBDIR}"
mkdir -p "$RESULTS_DIR"

mapfile -t TRACE_LIST < <(find "$TRACE_DIR" -maxdepth 1 -type f \( -name "*.champsimtrace.xz" -o -name "*.trace.gz" \) | sort)

if [ "${#TRACE_LIST[@]}" -eq 0 ]; then
    echo "[ERROR] No trace files found in: $TRACE_DIR"
    exit 1
fi

echo "[INFO] Found ${#TRACE_LIST[@]} traces"
echo "[INFO] Results will be written to: $RESULTS_DIR"
echo "[INFO] Running with MAX_JOBS=$MAX_JOBS"

run_trace() {
    local trace_path=$1
    local trace_name
    trace_name=$(basename "$trace_path")
    local output_name="${trace_name}-${BINARY}.txt"

    echo "[RUN] ${trace_name}"
    ./run_champsim.sh "$BINARY" "$N_WARM" "$N_SIM" "$TRACE_DIR" "$trace_name"

    local default_output="results_${N_SIM}M/${trace_name}-${BINARY}.txt"
    if [ -f "$default_output" ]; then
        mv "$default_output" "${RESULTS_DIR}/${output_name}"
    else
        echo "[WARN] Expected output not found for ${trace_name}: ${default_output}"
    fi
}

active_jobs=0
for trace_path in "${TRACE_LIST[@]}"; do
    run_trace "$trace_path" &
    active_jobs=$((active_jobs + 1))

    if [ "$active_jobs" -ge "$MAX_JOBS" ]; then
        wait -n
        active_jobs=$((active_jobs - 1))
    fi
done

wait

echo "[DONE] Completed ${#TRACE_LIST[@]} traces"
echo "[DONE] Output directory: $RESULTS_DIR"
