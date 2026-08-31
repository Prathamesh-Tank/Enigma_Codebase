import math
import re
import sys
from pathlib import Path

import pandas as pd


ENIGMA_ROOT = Path(__file__).resolve().parents[1]
PERF_ROOT = ENIGMA_ROOT.parent
OUTPUT_DIR = ENIGMA_ROOT / "compare_outputs"

SINGLE_TRACE_CSV = OUTPUT_DIR / "singlecore_trace_summary.csv"
SINGLE_BENCH_CSV = OUTPUT_DIR / "singlecore_benchmark_summary.csv"
SINGLE_SUITE_CSV = OUTPUT_DIR / "singlecore_suite_summary.csv"
DEADBLOCK_TRACE_CSV = OUTPUT_DIR / "deadblock_trace_summary.csv"
DEADBLOCK_BENCH_CSV = OUTPUT_DIR / "deadblock_benchmark_summary.csv"
MULTI_TRACE_CSV = OUTPUT_DIR / "multicore_trace_summary.csv"
MULTI_BENCH_CSV = OUTPUT_DIR / "multicore_benchmark_summary.csv"
MULTI_SUITE_CSV = OUTPUT_DIR / "multicore_suite_summary.csv"

ENIGMA_MODES = {
    "srrip": {
        "deadblock_spec": ENIGMA_ROOT / "results" / "srrip_1core_2MB_spec",
        "deadblock_gap": ENIGMA_ROOT / "results" / "srrip_1core_2MB_gap",
        "single_spec": ENIGMA_ROOT / "results" / "srrip_1core_16MB_8slices_spec",
        "single_gap": ENIGMA_ROOT / "results" / "srrip_1core_16MB_8slices_gap",
        "multi_spec": ENIGMA_ROOT / "results" / "srrip_8core_16MB_spec",
        "multi_gap": ENIGMA_ROOT / "results" / "srrip_8core_16MB_gap",
        "config": "16MB_8slice_baseline",
    },
    "mirage": {
        "deadblock_spec": ENIGMA_ROOT / "results" / "mirage_1core_2MB_spec",
        "deadblock_gap": ENIGMA_ROOT / "results" / "mirage_1core_2MB_gap",
        "single_spec": ENIGMA_ROOT / "results" / "mirage_1core_16MB_8slices_spec",
        "single_gap": ENIGMA_ROOT / "results" / "mirage_1core_16MB_8slices_gap",
        "multi_spec": ENIGMA_ROOT / "results" / "mirage_8core_16MB_spec",
        "multi_gap": ENIGMA_ROOT / "results" / "mirage_8core_16MB_gap",
        "config": "16MB_8slice_secure",
    },
    "enigma": {
        "deadblock_spec": ENIGMA_ROOT / "results" / "enigma_1core_2MB_spec",
        "deadblock_gap": ENIGMA_ROOT / "results" / "enigma_1core_2MB_gap",
        "single_spec": ENIGMA_ROOT / "results" / "enigma_1core_16MB_8slices_spec",
        "single_gap": ENIGMA_ROOT / "results" / "enigma_1core_16MB_8slices_gap",
        "multi_spec": ENIGMA_ROOT / "results" / "enigma_8core_16MB_spec",
        "multi_gap": ENIGMA_ROOT / "results" / "enigma_8core_16MB_gap",
        "config": "16MB_8slice_secure",
    },
}

MAYA_DIRS = {
    "single_spec": PERF_ROOT / "maya" / "results" / "maya_1core_12MB_8slices_spec",
    "single_gap": PERF_ROOT / "maya" / "results" / "maya_1core_12MB_8slices_gap",
    "multi_spec": PERF_ROOT / "maya" / "results" / "maya_8core_12MB_spec",
    "multi_gap": PERF_ROOT / "maya" / "results" / "maya_8core_12MB_gap",
    "config": "12MB_3way_8slice_maya",
}

ENIGMA_MAYA_DIRS = {
    "single_spec": PERF_ROOT / "enigma+maya" / "results" / "enigma_maya_1core_12MB_8slices_spec",
    "single_gap": PERF_ROOT / "enigma+maya" / "results" / "enigma_maya_1core_12MB_8slices_gap",
    "multi_spec": PERF_ROOT / "enigma+maya" / "results" / "enigma_maya_8core_12MB_spec",
    "multi_gap": PERF_ROOT / "enigma+maya" / "results" / "enigma_maya_8core_12MB_gap",
    "config": "12MB_3way_8slice_enigma_maya",
}


def search(pattern, text, cast=None, flags=0):
    match = re.search(pattern, text, flags)
    if not match:
        return None
    value = match.group(1)
    return cast(value) if cast is not None else value


def geometric_mean(series):
    values = [value for value in series if pd.notna(value) and value > 0]
    if not values:
        return math.nan
    return math.exp(sum(math.log(value) for value in values) / len(values))


def infer_suite(trace_name):
    if trace_name.startswith(("bc-", "bfs-", "cc-", "pr-", "sssp-")):
        return "gap"
    prefix = trace_name[:3]
    if prefix.isdigit():
        value = int(prefix)
        if 400 <= value < 500:
            return "spec2006"
        if 600 <= value < 700:
            return "spec2017"
    return "unknown"


def benchmark_name(trace_name):
    if trace_name.startswith(("bc-", "bfs-", "cc-", "pr-", "sssp-")):
        return trace_name.split("-", 1)[0]
    match = re.match(r"^\d+\.(.+?)(?:_s)?-", trace_name)
    return match.group(1) if match else trace_name


def strip_result_suffix(filename):
    base = filename[:-4] if filename.endswith(".txt") else filename
    match = re.match(r"^(.*)_\d+M_\d+M$", base)
    return match.group(1) if match else base


def parse_cache_line(text, cache_name, access_type):
    pattern = (
        rf"{cache_name}\s+{access_type}\s+ACCESS:\s+(\d+)\s+HIT:\s+(\d+)\s+MISS:\s+(\d+)"
        rf"\s+HIT %:\s+([0-9eE\.\+\-]+)\s+MISS %:\s+([0-9eE\.\+\-]+)"
        rf"\s+AVERAGE MISS PENALTY:\s+([0-9eE\.\+\-]+)"
    )
    match = re.search(pattern, text)
    if not match:
        return {}
    return {
        f"{cache_name}_{access_type}_access": int(match.group(1)),
        f"{cache_name}_{access_type}_hit": int(match.group(2)),
        f"{cache_name}_{access_type}_miss": int(match.group(3)),
        f"{cache_name}_{access_type}_hit_pct": float(match.group(4)),
        f"{cache_name}_{access_type}_miss_pct": float(match.group(5)),
        f"{cache_name}_{access_type}_avg_miss_penalty": float(match.group(6)),
    }


def parse_histogram_line(text, pattern, prefix, max_bin):
    line = search(pattern, text, flags=re.M)
    data = {}
    if not line:
        for index in range(max_bin + 1):
            data[f"{prefix}_{index}"] = None
        return data
    for index in range(max_bin + 1):
        data[f"{prefix}_{index}"] = search(rf"\[{index}\]=([0-9eE\.\+\-]+)", line, cast=float)
    return data


def parse_last_ipcs(text):
    cpu_ipcs = {}
    for cpu, ipc in re.findall(r"CPU\s+(\d+)\s+cumulative IPC:\s+([0-9eE\.\+\-]+)", text):
        cpu_ipcs[int(cpu)] = float(ipc)
    return cpu_ipcs


def parse_singlecore_row(mode, trace_name, text, config_name, source_dir):
    suite = infer_suite(trace_name)
    row = {
        "trace": trace_name,
        "benchmark": benchmark_name(trace_name),
        "suite": suite,
        "mode": mode,
        "config": config_name,
        "source_dir": source_dir,
        "llc_security_mode": search(r"LLC_SECURITY_MODE:(\S+)", text),
        "ipc": search(r"CPU 0 cumulative IPC: ([0-9eE\.\+\-]+)", text, cast=float),
        "instructions": search(r"CPU 0 cumulative IPC: [0-9eE\.\+\-]+ instructions: (\d+)", text, cast=int),
        "cycles": search(r"CPU 0 cumulative IPC: [0-9eE\.\+\-]+ instructions: \d+ cycles: (\d+)", text, cast=int),
        "llc_avg_miss_latency": search(r"LLC0 AVERAGE MISS LATENCY: ([0-9eE\.\+\-]+)", text, cast=float),
        "dram_pages": search(r"DRAM PAGES: (\d+)", text, cast=int),
        "allocated_pages": search(r"Allocated PAGES: (\d+)", text, cast=int),
        "deadblock_percentage": search(r"Deadblock percentage\s*:\s*([0-9eE\.\+\-]+)", text, cast=float),
    }

    for access_type in ["TOTAL", "LOAD", "RFO", "WRITEBACK"]:
        row.update(parse_cache_line(text, "LLC0", access_type))
        row.update(parse_cache_line(text, "L2C", access_type))
        row.update(parse_cache_line(text, "L1D", access_type))

    total_miss = row.get("LLC0_TOTAL_miss")
    instructions = row.get("instructions")
    row["mpki"] = (total_miss * 1000.0 / instructions) if total_miss is not None and instructions else None

    row["data_store_fills_total"] = search(r"Data-Store Fills: total=([0-9eE\.\+\-]+)", text, cast=float)
    row["data_store_fills_min"] = search(r"Data-Store Fills: .*min=([0-9eE\.\+\-]+)", text, cast=float)
    row["data_store_fills_max"] = search(r"Data-Store Fills: .*max=([0-9eE\.\+\-]+)", text, cast=float)
    row["data_store_fills_avg"] = search(r"Data-Store Fills: .*avg=([0-9eE\.\+\-]+)", text, cast=float)
    row["data_store_fills_cv"] = search(r"Data-Store Fills: .*cv=([0-9eE\.\+\-]+)", text, cast=float)
    row["data_store_evictions"] = search(r"Data-Store Evictions: ([0-9eE\.\+\-]+)", text, cast=float)

    row.update(
        parse_histogram_line(
            text,
            r"(LLC0 (?:Enigma|Mirage|SRRIP) Data-Store Occupancy Histogram: .*)",
            "data_store_occupancy",
            16,
        )
    )
    row.update(
        parse_histogram_line(
            text,
            r"(LLC0 (?:Enigma|SRRIP) Final RRPV Histogram: .*)",
            "final_rrpv",
            7,
        )
    )
    row.update(
        parse_histogram_line(
            text,
            r"(LLC0 (?:Enigma|SRRIP) Victim RRPV Histogram: .*)",
            "victim_rrpv",
            7,
        )
    )

    row["avg_rrpv_increment_rounds"] = search(r"Avg RRPV Increment Rounds Per Eviction: ([0-9eE\.\+\-]+)", text, cast=float)
    row["rrpv_total_rounds"] = search(r"total_rounds=([0-9eE\.\+\-]+)", text, cast=float)
    row["rrpv_sampled_evictions"] = search(r"sampled_evictions=([0-9eE\.\+\-]+)", text, cast=float)
    row["tag_store_full_events"] = search(r"Tag-Store Full Events: ([0-9eE\.\+\-]+)", text, cast=float)
    row["tag_insert_skew0"] = search(r"Tag Inserts By Skew: skew0=([0-9eE\.\+\-]+)", text, cast=float)
    row["tag_insert_skew1"] = search(r"Tag Inserts By Skew: skew0=[0-9eE\.\+\-]+ skew1=([0-9eE\.\+\-]+)", text, cast=float)
    row["tag_occ_skew0_avg"] = search(r"Tag Occupancy: skew0_avg=([0-9eE\.\+\-]+)", text, cast=float)
    row["tag_occ_skew1_avg"] = search(r"Tag Occupancy: .*skew1_avg=([0-9eE\.\+\-]+)", text, cast=float)
    row["tag_free_skew0_avg"] = search(r"Tag Occupancy: .*skew0_free_avg=([0-9eE\.\+\-]+)", text, cast=float)
    row["tag_free_skew1_avg"] = search(r"Tag Occupancy: .*skew1_free_avg=([0-9eE\.\+\-]+)", text, cast=float)
    row["tag_utilization"] = search(r"Tag Occupancy: .*utilization=([0-9eE\.\+\-]+)", text, cast=float)
    row["ssl_common_selections"] = search(r"Path Selection: ssl_common=([0-9eE\.\+\-]+)", text, cast=float)
    row["sos_forced_selections"] = search(r"Path Selection: .*deferred_sos=([0-9eE\.\+\-]+)", text, cast=float)
    row["common_path_rate"] = search(r"Path Selection: .*common_path_rate=([0-9eE\.\+\-]+)", text, cast=float)
    row["sos_service_rate"] = search(r"Path Selection: .*sos_service_rate=([0-9eE\.\+\-]+)", text, cast=float)
    row["deferred_sos_services"] = search(r"Deferred SoS Services: ([0-9eE\.\+\-]+)", text, cast=float)
    row["deferred_sos_dirty_writebacks"] = search(r"Deferred SoS Dirty Writebacks: ([0-9eE\.\+\-]+)", text, cast=float)
    row["sos_queue_enqueues"] = search(r"SoS Queue: enqueues=([0-9eE\.\+\-]+)", text, cast=float)
    row["sos_queue_max_occupancy"] = search(r"SoS Queue: .*max_occupancy=([0-9eE\.\+\-]+)", text, cast=float)
    row["sos_queue_remaining"] = search(r"SoS Queue: .*remaining=([0-9eE\.\+\-]+)", text, cast=float)
    row["stale_tag_repairs"] = search(r"Metadata Repairs: stale_tag_repairs=([0-9eE\.\+\-]+)", text, cast=float)
    row["no_of_sos_triggered"] = search(r"no_of_sos_triggered: ([0-9eE\.\+\-]+)", text, cast=float)
    row["total_miss_at_tag_array"] = search(r"total_miss_at_tag_array: ([0-9eE\.\+\-]+)", text, cast=float)
    row["sos_percentage"] = search(r"SoS_percentage: ([0-9eE\.\+\-]+)", text, cast=float)
    return row


def parse_multicore_row(mode, trace_name, text, config_name, source_dir):
    suite = infer_suite(trace_name)
    cpu_ipcs = parse_last_ipcs(text)
    row = {
        "trace": trace_name,
        "benchmark": benchmark_name(trace_name),
        "suite": suite,
        "mode": mode,
        "config": config_name,
        "source_dir": source_dir,
        "raw_ipc": sum(cpu_ipcs.values()) if cpu_ipcs else None,
    }
    for cpu in range(8):
        row[f"cpu{cpu}_ipc"] = cpu_ipcs.get(cpu)
    return row


def collect_result_rows(result_dir, parser, mode, config_name):
    rows = []
    if not result_dir.exists():
        print(f"Skipping missing directory: {result_dir}")
        return rows
    for result_file in sorted(result_dir.glob("*.txt")):
        trace_name = strip_result_suffix(result_file.name)
        text = result_file.read_text(errors="ignore")
        rows.append(parser(mode, trace_name, text, config_name, str(result_dir.relative_to(PERF_ROOT))))
    return rows


def collect_old_singlecore_rows():
    rows = []
    packaged_dir = ENIGMA_ROOT / "alltraces_enigma"
    pattern = re.compile(r"^(?P<trace>.*)-bimodal-no-no-no-(?P<mode>enigma|mirage|srrip)-0-1-1-3-0-1-1core-1core_llc\.txt$")
    if packaged_dir.exists():
        for result_file in sorted(packaged_dir.glob("*.txt")):
            match = pattern.match(result_file.name)
            if not match:
                continue
            mode = match.group("mode")
            text = result_file.read_text(errors="ignore")
            rows.append(
                parse_singlecore_row(
                    mode,
                    match.group("trace"),
                    text,
                    ENIGMA_MODES[mode]["config"],
                    str(packaged_dir.relative_to(PERF_ROOT)),
                )
            )
    for key in ["single_spec", "single_gap"]:
        rows.extend(collect_result_rows(MAYA_DIRS[key], parse_singlecore_row, "maya", MAYA_DIRS["config"]))
        rows.extend(collect_result_rows(ENIGMA_MAYA_DIRS[key], parse_singlecore_row, "enigma_maya", ENIGMA_MAYA_DIRS["config"]))
    return rows


def add_singlecore_normalizations(df):
    pivot = df.pivot_table(index="trace", columns="mode", values="ipc", aggfunc="first")
    rows = []
    for trace_name, pivot_row in pivot.iterrows():
        srrip_ipc = pivot_row.get("srrip")
        mirage_ipc = pivot_row.get("mirage")
        for mode in ["srrip", "mirage", "maya", "enigma_maya", "enigma"]:
            ipc_value = pivot_row.get(mode)
            rows.append(
                {
                    "trace": trace_name,
                    "mode": mode,
                    "ipc_norm_vs_srrip": ipc_value / srrip_ipc if pd.notna(ipc_value) and pd.notna(srrip_ipc) and srrip_ipc else math.nan,
                    "ipc_norm_vs_mirage": ipc_value / mirage_ipc if pd.notna(ipc_value) and pd.notna(mirage_ipc) and mirage_ipc else math.nan,
                }
            )
    return df.merge(pd.DataFrame(rows), on=["trace", "mode"], how="left")


def add_multicore_weighted_speedup(multicore_df, singlecore_df):
    single_lookup = singlecore_df[["trace", "mode", "ipc"]].rename(columns={"ipc": "singlecore_ipc"})
    merged = multicore_df.merge(single_lookup, on=["trace", "mode"], how="left")
    merged["weighted_speedup"] = merged["raw_ipc"] / merged["singlecore_ipc"]

    srrip_lookup = (
        merged[merged["mode"] == "srrip"][["trace", "weighted_speedup"]]
        .rename(columns={"weighted_speedup": "srrip_weighted_speedup"})
    )
    mirage_lookup = (
        merged[merged["mode"] == "mirage"][["trace", "weighted_speedup"]]
        .rename(columns={"weighted_speedup": "mirage_weighted_speedup"})
    )
    merged = merged.merge(srrip_lookup, on="trace", how="left")
    merged = merged.merge(mirage_lookup, on="trace", how="left")
    merged["weighted_speedup_norm_vs_srrip"] = merged["weighted_speedup"] / merged["srrip_weighted_speedup"]
    merged["weighted_speedup_norm_vs_mirage"] = merged["weighted_speedup"] / merged["mirage_weighted_speedup"]
    return merged


def write_singlecore_outputs(df):
    benchmark_df = (
        df.groupby(["suite", "benchmark", "mode", "config"], dropna=False)
        .agg(
            trace_count=("trace", "count"),
            ipc_mean=("ipc", "mean"),
            ipc_geomean=("ipc", geometric_mean),
            ipc_norm_vs_srrip_geomean=("ipc_norm_vs_srrip", geometric_mean),
            ipc_norm_vs_mirage_geomean=("ipc_norm_vs_mirage", geometric_mean),
            llc_hit_pct_mean=("LLC0_TOTAL_hit_pct", "mean"),
            mpki_mean=("mpki", "mean"),
            llc_avg_miss_latency_mean=("llc_avg_miss_latency", "mean"),
            data_store_fills_cv_mean=("data_store_fills_cv", "mean"),
            tag_utilization_mean=("tag_utilization", "mean"),
            sos_service_rate_mean=("sos_service_rate", "mean"),
        )
        .reset_index()
    )

    suite_df = (
        df.groupby(["suite", "mode", "config"], dropna=False)
        .agg(
            trace_count=("trace", "count"),
            ipc_mean=("ipc", "mean"),
            ipc_geomean=("ipc", geometric_mean),
            ipc_norm_vs_srrip_geomean=("ipc_norm_vs_srrip", geometric_mean),
            ipc_norm_vs_mirage_geomean=("ipc_norm_vs_mirage", geometric_mean),
            llc_hit_pct_mean=("LLC0_TOTAL_hit_pct", "mean"),
            llc_miss_pct_mean=("LLC0_TOTAL_miss_pct", "mean"),
            mpki_mean=("mpki", "mean"),
            llc_avg_miss_latency_mean=("llc_avg_miss_latency", "mean"),
            data_store_fills_cv_mean=("data_store_fills_cv", "mean"),
            tag_utilization_mean=("tag_utilization", "mean"),
            sos_service_rate_mean=("sos_service_rate", "mean"),
        )
        .reset_index()
    )

    df.sort_values(["suite", "benchmark", "trace", "mode"]).to_csv(SINGLE_TRACE_CSV, index=False)
    benchmark_df.sort_values(["suite", "benchmark", "mode"]).to_csv(SINGLE_BENCH_CSV, index=False)
    suite_df.sort_values(["suite", "mode"]).to_csv(SINGLE_SUITE_CSV, index=False)


def write_deadblock_outputs(df):
    benchmark_df = (
        df.groupby(["suite", "benchmark", "mode", "config"], dropna=False)
        .agg(
            trace_count=("trace", "count"),
            deadblock_percentage_mean=("deadblock_percentage", "mean"),
        )
        .reset_index()
    )

    df.sort_values(["suite", "benchmark", "trace", "mode"]).to_csv(DEADBLOCK_TRACE_CSV, index=False)
    benchmark_df.sort_values(["suite", "benchmark", "mode"]).to_csv(DEADBLOCK_BENCH_CSV, index=False)


def write_multicore_outputs(df):
    benchmark_df = (
        df.groupby(["suite", "benchmark", "mode", "config"], dropna=False)
        .agg(
            trace_count=("trace", "count"),
            raw_ipc_mean=("raw_ipc", "mean"),
            weighted_speedup_mean=("weighted_speedup", "mean"),
            weighted_speedup_geomean=("weighted_speedup", geometric_mean),
            weighted_speedup_norm_vs_srrip_geomean=("weighted_speedup_norm_vs_srrip", geometric_mean),
            weighted_speedup_norm_vs_mirage_geomean=("weighted_speedup_norm_vs_mirage", geometric_mean),
        )
        .reset_index()
    )

    suite_df = (
        df.groupby(["suite", "mode", "config"], dropna=False)
        .agg(
            trace_count=("trace", "count"),
            raw_ipc_mean=("raw_ipc", "mean"),
            weighted_speedup_mean=("weighted_speedup", "mean"),
            weighted_speedup_geomean=("weighted_speedup", geometric_mean),
            weighted_speedup_norm_vs_srrip_geomean=("weighted_speedup_norm_vs_srrip", geometric_mean),
            weighted_speedup_norm_vs_mirage_geomean=("weighted_speedup_norm_vs_mirage", geometric_mean),
        )
        .reset_index()
    )

    df.sort_values(["suite", "benchmark", "trace", "mode"]).to_csv(MULTI_TRACE_CSV, index=False)
    benchmark_df.sort_values(["suite", "benchmark", "mode"]).to_csv(MULTI_BENCH_CSV, index=False)
    suite_df.sort_values(["suite", "mode"]).to_csv(MULTI_SUITE_CSV, index=False)


def main():
    old_mode = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if old_mode == 1:
        single_rows = collect_old_singlecore_rows()
        deadblock_rows = []
        multicore_rows = []
    else:
        single_rows = []
        deadblock_rows = []
        multicore_rows = []

        for mode, config in ENIGMA_MODES.items():
            single_rows.extend(collect_result_rows(config["single_spec"], parse_singlecore_row, mode, config["config"]))
            single_rows.extend(collect_result_rows(config["single_gap"], parse_singlecore_row, mode, config["config"]))
            deadblock_rows.extend(collect_result_rows(config["deadblock_spec"], parse_singlecore_row, mode, config["config"]))
            deadblock_rows.extend(collect_result_rows(config["deadblock_gap"], parse_singlecore_row, mode, config["config"]))
            multicore_rows.extend(collect_result_rows(config["multi_spec"], parse_multicore_row, mode, config["config"]))
            multicore_rows.extend(collect_result_rows(config["multi_gap"], parse_multicore_row, mode, config["config"]))

        single_rows.extend(collect_result_rows(MAYA_DIRS["single_spec"], parse_singlecore_row, "maya", MAYA_DIRS["config"]))
        single_rows.extend(collect_result_rows(MAYA_DIRS["single_gap"], parse_singlecore_row, "maya", MAYA_DIRS["config"]))
        multicore_rows.extend(collect_result_rows(MAYA_DIRS["multi_spec"], parse_multicore_row, "maya", MAYA_DIRS["config"]))
        multicore_rows.extend(collect_result_rows(MAYA_DIRS["multi_gap"], parse_multicore_row, "maya", MAYA_DIRS["config"]))
        single_rows.extend(collect_result_rows(ENIGMA_MAYA_DIRS["single_spec"], parse_singlecore_row, "enigma_maya", ENIGMA_MAYA_DIRS["config"]))
        single_rows.extend(collect_result_rows(ENIGMA_MAYA_DIRS["single_gap"], parse_singlecore_row, "enigma_maya", ENIGMA_MAYA_DIRS["config"]))
        multicore_rows.extend(collect_result_rows(ENIGMA_MAYA_DIRS["multi_spec"], parse_multicore_row, "enigma_maya", ENIGMA_MAYA_DIRS["config"]))
        multicore_rows.extend(collect_result_rows(ENIGMA_MAYA_DIRS["multi_gap"], parse_multicore_row, "enigma_maya", ENIGMA_MAYA_DIRS["config"]))

    if not single_rows:
        raise SystemExit("No single-core results found. Run ./run_enigma.sh first or use ./plot_enigma.sh 1 for packaged single-core inputs.")

    single_df = add_singlecore_normalizations(pd.DataFrame(single_rows))
    write_singlecore_outputs(single_df)

    if deadblock_rows:
        write_deadblock_outputs(pd.DataFrame(deadblock_rows))

    if multicore_rows:
        multicore_df = add_multicore_weighted_speedup(pd.DataFrame(multicore_rows), single_df)
        write_multicore_outputs(multicore_df)

    print(f"Wrote {SINGLE_TRACE_CSV}")
    print(f"Wrote {SINGLE_BENCH_CSV}")
    print(f"Wrote {SINGLE_SUITE_CSV}")
    if deadblock_rows:
        print(f"Wrote {DEADBLOCK_TRACE_CSV}")
        print(f"Wrote {DEADBLOCK_BENCH_CSV}")
    if multicore_rows:
        print(f"Wrote {MULTI_TRACE_CSV}")
        print(f"Wrote {MULTI_BENCH_CSV}")
        print(f"Wrote {MULTI_SUITE_CSV}")


if __name__ == "__main__":
    main()
