#!/bin/bash

set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

mkdir -p "${ROOT_DIR}/enigma/results"
mkdir -p "${ROOT_DIR}/enigma+maya/results"
mkdir -p "${ROOT_DIR}/maya/results"

cd "${ROOT_DIR}/enigma"

echo "Running SRRIP single-core 2MB SPEC deadblock traces"
./run_1core_spec.sh bin/srrip_1core_2MB 200 200 srrip_1core_2MB_spec

echo "Running SRRIP single-core 2MB GAP deadblock traces"
./run_1core_gap.sh bin/srrip_1core_2MB 200 200 srrip_1core_2MB_gap

echo "Running Mirage single-core 2MB SPEC deadblock traces"
./run_1core_spec.sh bin/mirage_1core_2MB 200 200 mirage_1core_2MB_spec

echo "Running Mirage single-core 2MB GAP deadblock traces"
./run_1core_gap.sh bin/mirage_1core_2MB 200 200 mirage_1core_2MB_gap

echo "Running Enigma single-core 2MB SPEC deadblock traces"
./run_1core_spec.sh bin/enigma_1core_2MB 200 200 enigma_1core_2MB_spec

echo "Running Enigma single-core 2MB GAP deadblock traces"
./run_1core_gap.sh bin/enigma_1core_2MB 200 200 enigma_1core_2MB_gap

echo "Running Enigma single-core 16MB 8-slice SPEC traces"
./run_1core_spec.sh bin/enigma_1core_16MB_8slices 200 200 enigma_1core_16MB_8slices_spec

echo "Running Enigma single-core 16MB 8-slice GAP traces"
./run_1core_gap.sh bin/enigma_1core_16MB_8slices 200 200 enigma_1core_16MB_8slices_gap

echo "Running Mirage single-core 16MB 8-slice SPEC traces"
./run_1core_spec.sh bin/mirage_1core_16MB_8slices 200 200 mirage_1core_16MB_8slices_spec

echo "Running Mirage single-core 16MB 8-slice GAP traces"
./run_1core_gap.sh bin/mirage_1core_16MB_8slices 200 200 mirage_1core_16MB_8slices_gap

echo "Running baseline SRRIP single-core 16MB 8-slice SPEC traces"
./run_1core_spec.sh bin/srrip_1core_16MB_8slices 200 200 srrip_1core_16MB_8slices_spec

echo "Running baseline SRRIP single-core 16MB 8-slice GAP traces"
./run_1core_gap.sh bin/srrip_1core_16MB_8slices 200 200 srrip_1core_16MB_8slices_gap

echo "Running Enigma homogeneous 8-core 16MB SPEC traces"
./run_8core_spec.sh bin/enigma_8core_16MB 200 200 enigma_8core_16MB_spec

echo "Running Enigma homogeneous 8-core 16MB GAP traces"
./run_8core_gap.sh bin/enigma_8core_16MB 200 200 enigma_8core_16MB_gap

echo "Running Mirage homogeneous 8-core 16MB SPEC traces"
./run_8core_spec.sh bin/mirage_8core_16MB 200 200 mirage_8core_16MB_spec

echo "Running Mirage homogeneous 8-core 16MB GAP traces"
./run_8core_gap.sh bin/mirage_8core_16MB 200 200 mirage_8core_16MB_gap

echo "Running SRRIP homogeneous 8-core 16MB SPEC traces"
./run_8core_spec.sh bin/srrip_8core_16MB 200 200 srrip_8core_16MB_spec

echo "Running SRRIP homogeneous 8-core 16MB GAP traces"
./run_8core_gap.sh bin/srrip_8core_16MB 200 200 srrip_8core_16MB_gap

cd "${ROOT_DIR}/maya"

echo "Running Maya single-core 12MB 3-way 8-slice SPEC traces"
./run_1core_spec.sh bin/maya_1core_12MB_3way_8slices 200 200 maya_1core_12MB_8slices_spec

echo "Running Maya single-core 12MB 3-way 8-slice GAP traces"
./run_1core_gap.sh bin/maya_1core_12MB_3way_8slices 200 200 maya_1core_12MB_8slices_gap

echo "Running Maya homogeneous 8-core 12MB 3-way SPEC traces"
./run_8core_spec.sh bin/maya_8core_12MB_3way 200 200 maya_8core_12MB_spec

echo "Running Maya homogeneous 8-core 12MB 3-way GAP traces"
./run_8core_gap.sh bin/maya_8core_12MB_3way 200 200 maya_8core_12MB_gap

cd "${ROOT_DIR}/enigma+maya"

echo "Running Enigma+Maya single-core 12MB 3-way 8-slice SPEC traces"
./run_1core_spec.sh bin/enigma_maya_1core_12MB_3way_8slices 200 200 enigma_maya_1core_12MB_8slices_spec

echo "Running Enigma+Maya single-core 12MB 3-way 8-slice GAP traces"
./run_1core_gap.sh bin/enigma_maya_1core_12MB_3way_8slices 200 200 enigma_maya_1core_12MB_8slices_gap

echo "Running Enigma+Maya homogeneous 8-core 12MB 3-way SPEC traces"
./run_8core_spec.sh bin/enigma_maya_8core_12MB_3way 200 200 enigma_maya_8core_12MB_spec

echo "Running Enigma+Maya homogeneous 8-core 12MB 3-way GAP traces"
./run_8core_gap.sh bin/enigma_maya_8core_12MB_3way 200 200 enigma_maya_8core_12MB_gap

echo "All Enigma comparison runs have been launched"
