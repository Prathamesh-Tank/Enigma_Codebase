import csv
import os
import re
from pathlib import Path


RESULTS_DIR = Path(__file__).resolve().parents[1] / "results_200M_enigma_mirage_srrip"
OUTPUT_CSV = RESULTS_DIR / "enigma_mirage_srrip_200M_summary.csv"

FILE_RE = re.compile(
    r"^(?P<trace>.*)-bimodal-no-no-no-(?P<mode>enigma|mirage|srrip)-0-1-1-3-0-1-1core-1core_llc\.txt$"
)


def search(pattern, text, flags=0, cast=None):
    m = re.search(pattern, text, flags)
    if not m:
        return None
    value = m.group(1)
    if cast is not None:
        return cast(value)
    return value


def parse_cache_line(text, cache_name, access_type):
    prefix = rf"{cache_name}\s+{access_type}\s+ACCESS:\s+(\d+)\s+HIT:\s+(\d+)\s+MISS:\s+(\d+)\s+HIT %:\s+([0-9eE\.\+\-]+)\s+MISS %:\s+([0-9eE\.\+\-]+)\s+AVERAGE MISS PENALTY:\s+([0-9eE\.\+\-]+)"
    m = re.search(prefix, text)
    if not m:
        return {}
    return {
        f"{cache_name}_{access_type}_access": int(m.group(1)),
        f"{cache_name}_{access_type}_hit": int(m.group(2)),
        f"{cache_name}_{access_type}_miss": int(m.group(3)),
        f"{cache_name}_{access_type}_hit_pct": float(m.group(4)),
        f"{cache_name}_{access_type}_miss_pct": float(m.group(5)),
        f"{cache_name}_{access_type}_avg_miss_penalty": float(m.group(6)),
    }


def parse_histogram(line, prefix, max_bin):
    if not line:
        return {}
    out = {}
    for i in range(max_bin + 1):
        m = re.search(rf"\[{i}\]=([0-9eE\.\+\-]+)", line)
        out[f"{prefix}_{i}"] = float(m.group(1)) if m else None
    return out


def parse_result_file(filename):
    with open(filename, "r", errors="ignore") as f:
        text = f.read()
    m = FILE_RE.match(filename)
    if not m:
        return None

    row = {
        "trace": m.group("trace"),
        "mode": m.group("mode"),
        "llc_security_mode": search(r"LLC_SECURITY_MODE:(\S+)", text),
        "ipc": search(r"CPU 0 cumulative IPC: ([0-9eE\.\+\-]+)", text, cast=float),
        "instructions": search(r"CPU 0 cumulative IPC: [0-9eE\.\+\-]+ instructions: (\d+)", text, cast=int),
        "cycles": search(r"CPU 0 cumulative IPC: [0-9eE\.\+\-]+ instructions: \d+ cycles: (\d+)", text, cast=int),
        "llc_avg_miss_latency": search(r"LLC0 AVERAGE MISS LATENCY: ([0-9eE\.\+\-]+)", text, cast=float),
        "dram_pages": search(r"DRAM PAGES: (\d+)", text, cast=int),
        "allocated_pages": search(r"Allocated PAGES: (\d+)", text, cast=int),
        "major_fault": search(r"Major fault: (\d+)", text, cast=int),
        "minor_fault": search(r"Major fault: \d+ Minor fault: (\d+)", text, cast=int),
    }

    for access_type in ["TOTAL", "LOAD", "RFO", "WRITEBACK"]:
        row.update(parse_cache_line(text, "LLC0", access_type))
        row.update(parse_cache_line(text, "L2C", access_type))
        row.update(parse_cache_line(text, "L1D", access_type))

    data_fill_line = search(r"(LLC0 (?:Enigma|Mirage|SRRIP) Data-Store Fills: .*)", text, flags=re.M)
    row["data_store_fills_total"] = search(r"Data-Store Fills: total=([0-9eE\.\+\-]+)", data_fill_line or "", cast=float)
    row["data_store_fills_min"] = search(r"min=([0-9eE\.\+\-]+)", data_fill_line or "", cast=float)
    row["data_store_fills_max"] = search(r"max=([0-9eE\.\+\-]+)", data_fill_line or "", cast=float)
    row["data_store_fills_avg"] = search(r"avg=([0-9eE\.\+\-]+)", data_fill_line or "", cast=float)
    row["data_store_fills_cv"] = search(r"cv=([0-9eE\.\+\-]+)", data_fill_line or "", cast=float)
    row["data_store_evictions"] = search(r"Data-Store Evictions: ([0-9eE\.\+\-]+)", text, cast=float)

    occ_line = search(r"(LLC0 (?:Enigma|Mirage|SRRIP) Data-Store Occupancy Histogram: .*)", text, flags=re.M)
    row.update(parse_histogram(occ_line, "data_store_occupancy", 16))

    final_rrpv_line = search(r"(LLC0 (?:Enigma|SRRIP) Final RRPV Histogram: .*)", text, flags=re.M)
    victim_rrpv_line = search(r"(LLC0 (?:Enigma|SRRIP) Victim RRPV Histogram: .*)", text, flags=re.M)
    row.update(parse_histogram(final_rrpv_line, "final_rrpv", 7))
    row.update(parse_histogram(victim_rrpv_line, "victim_rrpv", 7))
    row["avg_rrpv_increment_rounds"] = search(r"Avg RRPV Increment Rounds Per Eviction: ([0-9eE\.\+\-]+)", text, cast=float)
    row["rrpv_total_rounds"] = search(r"total_rounds=([0-9eE\.\+\-]+)", text, cast=float)
    row["rrpv_sampled_evictions"] = search(r"sampled_evictions=([0-9eE\.\+\-]+)", text, cast=float)

    row["tag_store_full_events"] = search(r"Enigma Tag-Store Full Events: ([0-9eE\.\+\-]+)", text, cast=float)
    row["tag_insert_skew0"] = search(r"Tag Inserts By Skew: skew0=([0-9eE\.\+\-]+)", text, cast=float)
    row["tag_insert_skew1"] = search(r"Tag Inserts By Skew: skew0=[0-9eE\.\+\-]+ skew1=([0-9eE\.\+\-]+)", text, cast=float)
    row["tag_occ_skew0_avg"] = search(r"Tag Occupancy: skew0_avg=([0-9eE\.\+\-]+)", text, cast=float)
    row["tag_occ_skew1_avg"] = search(r"Tag Occupancy: .*skew1_avg=([0-9eE\.\+\-]+)", text, cast=float)
    row["tag_free_skew0_avg"] = search(r"Tag Occupancy: .*skew0_free_avg=([0-9eE\.\+\-]+)", text, cast=float)
    row["tag_free_skew1_avg"] = search(r"Tag Occupancy: .*skew1_free_avg=([0-9eE\.\+\-]+)", text, cast=float)
    row["tag_utilization"] = search(r"Tag Occupancy: .*utilization=([0-9eE\.\+\-]+)", text, cast=float)

    tag0_hist_line = search(r"(LLC0 (?:Enigma|Mirage) Tag Occupancy Histogram Skew0: .*)", text, flags=re.M)
    tag1_hist_line = search(r"(LLC0 (?:Enigma|Mirage) Tag Occupancy Histogram Skew1: .*)", text, flags=re.M)
    row.update(parse_histogram(tag0_hist_line, "tag_occ_skew0", 14))
    row.update(parse_histogram(tag1_hist_line, "tag_occ_skew1", 14))

    row["ssl_common_selections"] = search(r"Enigma Path Selection: ssl_common=([0-9eE\.\+\-]+)", text, cast=float)
    row["sos_forced_selections"] = search(r"Enigma Path Selection: .*deferred_sos=([0-9eE\.\+\-]+)", text, cast=float)
    row["common_path_rate"] = search(r"Enigma Path Selection: .*common_path_rate=([0-9eE\.\+\-]+)", text, cast=float)
    row["sos_service_rate"] = search(r"Enigma Path Selection: .*sos_service_rate=([0-9eE\.\+\-]+)", text, cast=float)
    row["deferred_sos_services"] = search(r"Enigma Deferred SoS Services: ([0-9eE\.\+\-]+)", text, cast=float)
    row["deferred_sos_dirty_writebacks"] = search(r"Enigma Deferred SoS Dirty Writebacks: ([0-9eE\.\+\-]+)", text, cast=float)
    row["sos_queue_enqueues"] = search(r"Enigma SoS Queue: enqueues=([0-9eE\.\+\-]+)", text, cast=float)
    row["sos_queue_max_occupancy"] = search(r"Enigma SoS Queue: .*max_occupancy=([0-9eE\.\+\-]+)", text, cast=float)
    row["sos_queue_remaining"] = search(r"Enigma SoS Queue: .*remaining=([0-9eE\.\+\-]+)", text, cast=float)
    row["stale_tag_repairs"] = search(r"Enigma Metadata Repairs: stale_tag_repairs=([0-9eE\.\+\-]+)", text, cast=float)
    row["no_of_sos_triggered"] = search(r"no_of_sos_triggered: ([0-9eE\.\+\-]+)", text, cast=float)
    row["total_miss_at_tag_array"] = search(r"total_miss_at_tag_array: ([0-9eE\.\+\-]+)", text, cast=float)
    row["sos_percentage"] = search(r"SoS_percentage: ([0-9eE\.\+\-]+)", text, cast=float)
    return row


def main():
    rows = []
    old_cwd = os.getcwd()
    os.chdir(RESULTS_DIR)
    try:
        for filename in sorted(fn for fn in os.listdir(".") if fn.endswith(".txt")):
            parsed = parse_result_file(filename)
            if parsed is not None:
                rows.append(parsed)
    finally:
        os.chdir(old_cwd)

    fieldnames = sorted({key for row in rows for key in row.keys()})
    with OUTPUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
