LLC mode is now selected at build time through LLC_Replacement.

Build ENIGMA:
./build_champsim.sh bimodal no no no enigma 1 0 -1 0 1 1 3 0 1 1

Build MIRAGE:
./build_champsim.sh bimodal no no no mirage 1 0 -1 0 1 1 3 0 1 1

Build plain non-randomized SRRIP:
./build_champsim.sh bimodal no no no srrip 1 0 -1 0 1 1 3 0 1 1

To run ENIGMA on DPC3 mcf:
./run_champsim.sh bimodal-no-no-no-enigma-0-1-1-3-0-1-1core-1core_llc 1 1 ../dpc3_traces 605.mcf_s-1554B.champsimtrace.xz

Current SoS threshold in inc/cache_mode.h:
ENIGMA_SOS_THRESHOLD = 2
