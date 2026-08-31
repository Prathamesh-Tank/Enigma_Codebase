from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ENIGMA_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ENIGMA_ROOT / "compare_outputs"

SINGLE_BENCH_CSV = OUTPUT_DIR / "singlecore_benchmark_summary.csv"
SINGLE_SUITE_CSV = OUTPUT_DIR / "singlecore_suite_summary.csv"
DEADBLOCK_BENCH_CSV = OUTPUT_DIR / "deadblock_benchmark_summary.csv"
MULTI_BENCH_CSV = OUTPUT_DIR / "multicore_benchmark_summary.csv"
MULTI_SUITE_CSV = OUTPUT_DIR / "multicore_suite_summary.csv"

MODE_ORDER = ["srrip", "mirage", "maya", "enigma_maya", "enigma"]
MODE_LABELS = {
    "srrip": "SRRIP",
    "mirage": "Mirage",
    "maya": "Maya",
    "enigma_maya": "Enigma+Maya",
    "enigma": "Enigma",
}
MODE_COLORS = {
    "srrip": "#4e79a7",
    "mirage": "#f28e2b",
    "maya": "#59a14f",
    "enigma_maya": "#b07aa1",
    "enigma": "#e15759",
}
SUITE_ORDER = ["spec2006", "spec2017", "gap", "unknown"]


def ordered_suites(df):
    return [suite for suite in SUITE_ORDER if suite in set(df["suite"])]


def plot_grouped_bars(df, x_key, metric, ylabel, title, filename, modes):
    groups = list(df[x_key].drop_duplicates())
    if not groups:
        return

    width = 0.18 if len(modes) >= 4 else 0.25
    x_positions = list(range(len(groups)))

    fig, ax = plt.subplots(figsize=(max(10, len(groups) * 0.35), 5))
    for index, mode in enumerate(modes):
        mode_df = df[df["mode"] == mode].set_index(x_key)
        values = [mode_df.loc[group, metric] if group in mode_df.index else float("nan") for group in groups]
        offset = (index - (len(modes) - 1) / 2.0) * width
        ax.bar(
            [x + offset for x in x_positions],
            values,
            width=width,
            label=MODE_LABELS[mode],
            color=MODE_COLORS[mode],
        )

    ax.set_xticks(x_positions)
    ax.set_xticklabels(groups, rotation=45, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(frameon=False, ncol=min(len(modes), 4))
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / filename)
    plt.close(fig)


def plot_suite_metric(df, metric, ylabel, title, filename, modes):
    suites = ordered_suites(df)
    if not suites:
        return

    width = 0.18 if len(modes) >= 4 else 0.25
    x_positions = list(range(len(suites)))

    fig, ax = plt.subplots(figsize=(10, 5))
    for index, mode in enumerate(modes):
        mode_df = df[df["mode"] == mode].set_index("suite")
        values = [mode_df.loc[suite, metric] if suite in mode_df.index else float("nan") for suite in suites]
        offset = (index - (len(modes) - 1) / 2.0) * width
        ax.bar(
            [x + offset for x in x_positions],
            values,
            width=width,
            label=MODE_LABELS[mode],
            color=MODE_COLORS[mode],
        )

    ax.set_xticks(x_positions)
    ax.set_xticklabels(suites)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(frameon=False, ncol=min(len(modes), 4))
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / filename)
    plt.close(fig)


def main():
    if SINGLE_SUITE_CSV.exists():
        single_suite_df = pd.read_csv(SINGLE_SUITE_CSV)
        plot_suite_metric(
            single_suite_df,
            "ipc_norm_vs_srrip_geomean",
            "Geomean IPC / SRRIP",
            "Single-Core Performance Normalized to SRRIP",
            "FigE1_singlecore_ipc_norm_vs_srrip.pdf",
            MODE_ORDER,
        )
        plot_suite_metric(
            single_suite_df,
            "llc_hit_pct_mean",
            "Average LLC Hit Rate (%)",
            "Single-Core LLC Hit Rate",
            "FigE2_singlecore_llc_hit_rate.pdf",
            MODE_ORDER,
        )
        plot_suite_metric(
            single_suite_df,
            "mpki_mean",
            "Average MPKI",
            "Single-Core MPKI",
            "FigE3_singlecore_mpki.pdf",
            "srrip mirage maya enigma_maya enigma".split(),
        )

    if DEADBLOCK_BENCH_CSV.exists():
        deadblock_df = pd.read_csv(DEADBLOCK_BENCH_CSV)
        plot_grouped_bars(
            deadblock_df,
            "benchmark",
            "deadblock_percentage_mean",
            "Deadblock Percentage",
            "Deadblock Comparison",
            "FigE4_deadblocks.pdf",
            ["srrip", "mirage", "enigma"],
        )

    if MULTI_SUITE_CSV.exists():
        multi_suite_df = pd.read_csv(MULTI_SUITE_CSV)
        plot_suite_metric(
            multi_suite_df,
            "weighted_speedup_norm_vs_srrip_geomean",
            "Geomean Weighted Speedup / SRRIP",
            "Homogeneous 8-Core Performance Normalized to SRRIP",
            "FigE5_multicore_weighted_speedup_norm_vs_srrip.pdf",
            MODE_ORDER,
        )

    if MULTI_BENCH_CSV.exists():
        multi_bench_df = pd.read_csv(MULTI_BENCH_CSV)
        plot_grouped_bars(
            multi_bench_df,
            "benchmark",
            "weighted_speedup_geomean",
            "Geomean Weighted Speedup",
            "Homogeneous 8-Core Weighted Speedup by Benchmark",
            "FigE6_multicore_weighted_speedup_by_benchmark.pdf",
            MODE_ORDER,
        )

    print(f"Wrote plots to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
