import argparse
import csv
import pathlib
import re


SUMMARY_HEADERS = [
    "design",
    "extra_ways_per_skew",
    "billion_tries",
    "seed",
    "total_iterations",
    "spill_count",
    "spill_percent",
    "cuckoo_spill_count",
    "cuckoo_spill_percent",
    "trials_per_spill",
    "replacement_mode",
    "ssl_total_replacements",
    "ssl_set_select_min",
    "ssl_set_select_max",
    "ssl_set_select_diff",
]

BUCKET_HEADERS = [
    "design",
    "extra_ways_per_skew",
    "billion_tries",
    "seed",
    "bucket_occupancy",
    "count",
    "prob_percent",
]

DEST_HEADERS = [
    "design",
    "extra_ways_per_skew",
    "billion_tries",
    "seed",
    "dest_bucket_occupancy",
    "insertions",
    "percent",
]


def parse_file(path: pathlib.Path):
    text = path.read_text(encoding="utf-8", errors="replace")

    file_match = re.match(
        r"(?P<design>.+)\.(?P<extra>\d+)extraways\.(?P<bn>\d+)Bn\.seed(?P<seed>\d+)\.out$",
        path.name,
    )
    if not file_match:
      raise ValueError(f"Unrecognized output filename: {path.name}")

    design = file_match.group("design")
    extra = int(file_match.group("extra"))
    billion_tries = int(file_match.group("bn"))
    seed = int(file_match.group("seed"))

    total_iterations = None
    m = re.search(r"BALL_THROWS:(\d+),\s*SEED:(\d+)", text)
    if m:
        total_iterations = int(m.group(1))
    else:
        m = re.search(r"INSTALLATIONS=(\d+),\s*SEED=(\d+)", text)
        if m:
            total_iterations = int(m.group(1))

    replacement_mode = ""
    m = re.search(r"Replacement:\s*(.+)", text)
    if m:
        replacement_mode = m.group(1).strip()
    elif design == "mirage":
        replacement_mode = "global random replacement"
    elif design == "maya":
        replacement_mode = "maya priority/reuse path"

    spill_count = 0
    spill_percent = 0.0
    m = re.search(r"Spill Count:\s+(\d+)\s+\(([\d.]+)%?\)", text)
    if m:
        spill_count = int(m.group(1))
        spill_percent = float(m.group(2))

    cuckoo_spill_count = 0
    cuckoo_spill_percent = 0.0
    m = re.search(r"Cuckoo Spill Count:\s+(\d+)\s+\(([\d.]+)%?\)", text)
    if m:
        cuckoo_spill_count = int(m.group(1))
        cuckoo_spill_percent = float(m.group(2))

    trials_per_spill = ""
    if spill_count > 0 and total_iterations is not None:
        trials_per_spill = total_iterations / spill_count

    ssl_total_replacements = ""
    ssl_set_select_min = ""
    ssl_set_select_max = ""
    ssl_set_select_diff = ""
    m = re.search(r"Total measured data-store replacements:\s+(\d+)", text)
    if m:
        ssl_total_replacements = int(m.group(1))
    m = re.search(r"Per-set SSL selections:\s+min=(\d+),\s+max=(\d+),\s+difference=(\d+)", text)
    if m:
        ssl_set_select_min = int(m.group(1))
        ssl_set_select_max = int(m.group(2))
        ssl_set_select_diff = int(m.group(3))

    bucket_rows = []
    bucket_section = re.search(
        r"P\(Bucket=k balls\)(.*?)(?:Distribution of Balls-in-Dest-Bucket|Distribution of Destination-Bucket Occupancy)",
        text,
        re.DOTALL,
    )
    if bucket_section:
        for occ, count, prob in re.findall(
            r"Bucket\[\s*(\d+)\s+Fill\]:\s+(\d+)\s+\(\s*([\d.]+)%?\)",
            bucket_section.group(1),
        ):
            bucket_rows.append({
                "design": design,
                "extra_ways_per_skew": extra,
                "billion_tries": billion_tries,
                "seed": seed,
                "bucket_occupancy": int(occ),
                "count": int(count),
                "prob_percent": float(prob),
            })

    dest_rows = []
    dest_section = re.search(
        r"(?:Balls-in-Dest-Bucket \(k\).*?\n|Balls in destination bucket \(k\).*?\n)(.*?)(?:Spill Count:)",
        text,
        re.DOTALL,
    )
    if dest_section:
        for occ, count, pct in re.findall(
            r"^\s*(\d+):\s+(\d+)\s+\(\s*([\d.]+)%?\)",
            dest_section.group(1),
            re.MULTILINE,
        ):
            dest_rows.append({
                "design": design,
                "extra_ways_per_skew": extra,
                "billion_tries": billion_tries,
                "seed": seed,
                "dest_bucket_occupancy": int(occ),
                "insertions": int(count),
                "percent": float(pct),
            })

    summary_row = {
        "design": design,
        "extra_ways_per_skew": extra,
        "billion_tries": billion_tries,
        "seed": seed,
        "total_iterations": total_iterations if total_iterations is not None else "",
        "spill_count": spill_count,
        "spill_percent": spill_percent,
        "cuckoo_spill_count": cuckoo_spill_count,
        "cuckoo_spill_percent": cuckoo_spill_percent,
        "trials_per_spill": trials_per_spill,
        "replacement_mode": replacement_mode,
        "ssl_total_replacements": ssl_total_replacements,
        "ssl_set_select_min": ssl_set_select_min,
        "ssl_set_select_max": ssl_set_select_max,
        "ssl_set_select_diff": ssl_set_select_diff,
    }

    return summary_row, bucket_rows, dest_rows


def write_csv(path: pathlib.Path, headers, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    input_dir = pathlib.Path(args.input_dir)
    output_dir = pathlib.Path(args.output_dir)

    summary_rows = []
    bucket_rows = []
    dest_rows = []

    for path in sorted(input_dir.glob("*.out")):
        summary_row, file_bucket_rows, file_dest_rows = parse_file(path)
        summary_rows.append(summary_row)
        bucket_rows.extend(file_bucket_rows)
        dest_rows.extend(file_dest_rows)

    write_csv(output_dir / "security_compare_summary.csv", SUMMARY_HEADERS, summary_rows)
    write_csv(output_dir / "security_compare_bucket_prob.csv", BUCKET_HEADERS, bucket_rows)
    write_csv(output_dir / "security_compare_dest_bucket.csv", DEST_HEADERS, dest_rows)


if __name__ == "__main__":
    main()
