#!/bin/bash

set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

mkdir -p "${ROOT_DIR}/enigma/bin"
mkdir -p "${ROOT_DIR}/enigma+maya/bin"
mkdir -p "${ROOT_DIR}/maya/bin"

echo "Building SRRIP single-core 2MB deadblock binary"
cd "${ROOT_DIR}/enigma"
./build_champsim.sh bimodal no no no srrip 1 0 -1 0 1 1 3 0 1 1 > build.log
mv -f bin/bimodal-no-no-no-srrip-0-1-1-3-0-1-1core-1core_llc bin/srrip_1core_2MB

echo "Building Mirage single-core 2MB deadblock binary"
./build_champsim.sh bimodal no no no mirage 1 0 -1 0 1 1 3 0 1 1 > build.log
mv -f bin/bimodal-no-no-no-mirage-0-1-1-3-0-1-1core-1core_llc bin/mirage_1core_2MB

echo "Building Enigma single-core 2MB deadblock binary"
./build_champsim.sh bimodal no no no enigma 1 0 -1 0 1 1 3 0 1 1 > build.log
mv -f bin/bimodal-no-no-no-enigma-0-1-1-3-0-1-1core-1core_llc bin/enigma_1core_2MB

echo "Building Enigma single-core 16MB 8-slice binary"
./build_champsim.sh bimodal no no no enigma 1 0 -1 0 1 1 3 0 1 8 > build.log
mv -f bin/bimodal-no-no-no-enigma-0-1-1-3-0-1-1core-8core_llc bin/enigma_1core_16MB_8slices

echo "Building Mirage single-core 16MB 8-slice binary"
./build_champsim.sh bimodal no no no mirage 1 0 -1 0 1 1 3 0 1 8 > build.log
mv -f bin/bimodal-no-no-no-mirage-0-1-1-3-0-1-1core-8core_llc bin/mirage_1core_16MB_8slices

echo "Building baseline SRRIP single-core 16MB 8-slice binary"
./build_champsim.sh bimodal no no no srrip 1 0 -1 0 1 1 3 0 1 8 > build.log
mv -f bin/bimodal-no-no-no-srrip-0-1-1-3-0-1-1core-8core_llc bin/srrip_1core_16MB_8slices

echo "Building Enigma homogeneous 8-core 16MB binary"
./build_champsim.sh bimodal no no no enigma 8 0 -2 0 1 1 3 0 1 1 > build.log
mv -f bin/bimodal-no-no-no-enigma-0-1-1-3-0-1-8core_mirage bin/enigma_8core_16MB

echo "Building Mirage homogeneous 8-core 16MB binary"
./build_champsim.sh bimodal no no no mirage 8 0 -2 0 1 1 3 0 1 1 > build.log
mv -f bin/bimodal-no-no-no-mirage-0-1-1-3-0-1-8core_mirage bin/mirage_8core_16MB

echo "Building SRRIP homogeneous 8-core 16MB binary"
./build_champsim.sh bimodal no no no srrip 8 0 -2 0 1 1 3 0 1 1 > build.log
mv -f bin/bimodal-no-no-no-srrip-0-1-1-3-0-1-8core_mirage bin/srrip_8core_16MB

echo "Building Maya single-core 12MB 3-way 8-slice binary"
cd "${ROOT_DIR}/maya"
./build_champsim.sh bimodal ipcp ipcp no hawkeye 1 0 -1 0 1 1 3 0 1 8 > build.log
mv -f bin/bimodal-ipcp-ipcp-no-hawkeye-0-1-1-3-0-1-1core-8core_maya bin/maya_1core_12MB_3way_8slices

echo "Building Maya homogeneous 8-core 12MB 3-way binary"
./build_champsim.sh bimodal ipcp ipcp no hawkeye 8 0 -2 0 1 1 3 0 1 1 > build.log
mv -f bin/bimodal-ipcp-ipcp-no-hawkeye-0-1-1-3-0-1-8core_maya bin/maya_8core_12MB_3way

echo "Building Enigma+Maya single-core 12MB 3-way 8-slice binary"
cd "${ROOT_DIR}/enigma+maya"
./build_champsim.sh bimodal ipcp ipcp no srrip 1 0 -1 0 1 1 3 0 1 8 > build.log
mv -f "bin/bimodal-ipcp-ipcp-no-srrip-0-1-1-3-0-1-1core-8core_enigma+maya" bin/enigma_maya_1core_12MB_3way_8slices

echo "Building Enigma+Maya homogeneous 8-core 12MB 3-way binary"
./build_champsim.sh bimodal ipcp ipcp no srrip 8 0 -2 0 1 1 3 0 1 1 > build.log
mv -f "bin/bimodal-ipcp-ipcp-no-srrip-0-1-1-3-0-1-8core_enigma+maya" bin/enigma_maya_8core_12MB_3way

echo "All Enigma comparison binaries are ready under performance-analysis/enigma/bin, performance-analysis/maya/bin, and performance-analysis/enigma+maya/bin"
