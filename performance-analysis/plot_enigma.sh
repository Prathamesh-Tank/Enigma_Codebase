#!/bin/bash

set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Usage: ./plot_enigma.sh [0|1]"
    echo "  0: parse freshly generated results from enigma/results and maya/results"
    echo "  1: parse packaged comparison results when available"
    exit 1
fi

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

cd "${ROOT_DIR}/enigma/scripts"

python3 get_compare_data.py "$1"
python3 get_compare_plots.py

cd "${ROOT_DIR}"

echo "Combined CSV and plots are available under performance-analysis/enigma/compare_outputs"
