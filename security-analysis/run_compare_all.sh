#!/usr/bin/env bash

set -euo pipefail

EXTRA_WAYS=(1 2 3 4 5 6)
BILLION_TRIES=1
SEED=1
OUTPUT_DIR=""
SMOKE_TEST=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --extra-ways)
      IFS=',' read -r -a EXTRA_WAYS <<< "$2"
      shift 2
      ;;
    --billion-tries)
      BILLION_TRIES="$2"
      shift 2
      ;;
    --seed)
      SEED="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --smoke-test)
      SMOKE_TEST=1
      shift
      ;;
    -h|--help)
      cat <<'EOF'
Usage: ./run_compare_all.sh [options]

Options:
  --extra-ways 1,2,3,4,5,6   Comma-separated extra ways per skew
  --billion-tries N          Number of 1B execution units to simulate
  --seed N                   RNG seed
  --output-dir PATH          Relative output directory under security-analysis
  --smoke-test               Build short-run binaries for validation
  -h, --help                 Show this help text
EOF
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$ROOT/bin"
SRC_DIR="$ROOT/src"

if [[ -z "$OUTPUT_DIR" ]]; then
  if [[ "$SMOKE_TEST" -eq 1 ]]; then
    OUTPUT_DIR="results/comparison_smoke"
  else
    OUTPUT_DIR="results/comparison_1Bn"
  fi
fi

OUT_DIR="$ROOT/$OUTPUT_DIR"
RAW_DIR="$OUT_DIR/raw_results"

mkdir -p "$BIN_DIR" "$RAW_DIR"

COMMON_FLAGS=(-std=c++0x -O3)
SMOKE_DEFINES=()
if [[ "$SMOKE_TEST" -eq 1 ]]; then
  SMOKE_DEFINES=(
    -DCUSTOM_BILLION_TRIES=1000000ULL
    -DCUSTOM_HUNDRED_MILLION_TRIES=100000ULL
  )
fi

BUILD_NAMES=(mirage maya ssl_local_random)
BUILD_SOURCES=(
  "$SRC_DIR/security_mirage.cpp"
  "$SRC_DIR/security_maya.cpp"
  "$SRC_DIR/bucketsNballs_SSL_LocalRandom_NBn.cpp"
)
BUILD_BINARIES=(
  "$BIN_DIR/mirage.o"
  "$BIN_DIR/maya6Ways.o"
  "$BIN_DIR/mirage_ssl_local_random.o"
)

for idx in "${!BUILD_NAMES[@]}"; do
  echo "Building ${BUILD_NAMES[$idx]}..."
  g++ "${COMMON_FLAGS[@]}" "${SMOKE_DEFINES[@]}" \
    "${BUILD_SOURCES[$idx]}" -o "${BUILD_BINARIES[$idx]}"
done

for extra in "${EXTRA_WAYS[@]}"; do
  for idx in "${!BUILD_NAMES[@]}"; do
    output_name="${BUILD_NAMES[$idx]}.${extra}extraways.${BILLION_TRIES}Bn.seed${SEED}.out"
    output_path="$RAW_DIR/$output_name"
    echo "Running ${BUILD_NAMES[$idx]} extra=$extra billion_tries=$BILLION_TRIES seed=$SEED"
    "${BUILD_BINARIES[$idx]}" "$extra" "$BILLION_TRIES" "$SEED" > "$output_path" 2>&1
  done
done

echo "Parsing comparison CSVs..."
python3 "$ROOT/scripts/export_security_compare_csv.py" \
  --input-dir "$RAW_DIR" \
  --output-dir "$OUT_DIR"

echo "Done. Results are in $OUT_DIR"
