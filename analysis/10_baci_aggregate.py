#!/usr/bin/env python3
"""
Our first research objective seeks to price two resource grabs on a single object, the world
trade network. To achieve this objective we must first construct that object, so this script
ingests CEPII BACI HS17 V202601 end to end and aggregates roughly 11 million HS6 records per
year into the bilateral panel every downstream script reads.

10_baci_aggregate.py -- BACI HS17 V202601 ingest + aggregation (end-to-end).

We download CEPII BACI HS17 V202601 if it is absent, then produce:
  1. data/processed/wtw_agg_2017_2024.csv
       Bilateral country x country TOTAL trade value per year, aggregated over
       all HS6 products. Columns: year, exporter_iso3, importer_iso3, value_kusd.
       value_kusd is in THOUSANDS of current USD (BACI's native 'v' unit).
  2. data/processed/baci_2024_hs6.parquet
       Full 2024 HS6-level file, columns t,i,j,k,v,q as shipped
       (k kept as 6-char string to preserve leading zeros). Snappy compression.
  3. data/processed/baci_country_codes.csv
       Country code <-> ISO3 mapping from the same release, plus an
       'iso3_recode' column where BACI code 490 "Other Asia, nes" -> TWN
       (BACI ships Taiwan under 490 with no usable ISO3).

Method notes:
  - We stream years ONE AT A TIME directly from the zip (zipfile member
    stream -> pandas chunked reader). No full extraction, no temp CSVs.
  - We delete the zip after successful processing unless --keep-zip is given.

Source:  https://www.cepii.fr/DATA_DOWNLOAD/baci/data/BACI_HS17_V202601.zip
License: Etalab 2.0 (CEPII open license)
Run:     python3 analysis/10_baci_aggregate.py [--keep-zip]
"""

import argparse
import io
import os
import subprocess
import sys
import zipfile

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw")
PROC_DIR = os.path.join(ROOT, "data", "processed")
ZIP_PATH = os.path.join(RAW_DIR, "BACI_HS17_V202601.zip")
ZIP_URL = "https://www.cepii.fr/DATA_DOWNLOAD/baci/data/BACI_HS17_V202601.zip"

VERSION = "V202601"
HS = "HS17"
YEARS = list(range(2017, 2025))          # 2017..2024 inclusive
PARQUET_YEAR = 2024
PULL_DATE = "2026-07-30"
CHUNKSIZE = 3_000_000

PROVENANCE = (
    "# source: CEPII BACI {hs} {ver} ({url})\n"
    "# pulled: {pulled}\n"
    "# license: Etalab 2.0\n"
    "# script: analysis/10_baci_aggregate.py\n"
).format(hs=HS, ver=VERSION, url=ZIP_URL, pulled=PULL_DATE)

PARQUET_SCHEMA = pa.schema(
    [
        ("t", pa.int32()),      # year
        ("i", pa.int32()),      # exporter (BACI country code)
        ("j", pa.int32()),      # importer (BACI country code)
        ("k", pa.string()),     # HS6 product code (string, leading zeros kept)
        ("v", pa.float64()),    # value, thousands of current USD
        ("q", pa.float64()),    # quantity, metric tons (NaN when missing)
    ]
)


def ensure_zip():
    if os.path.exists(ZIP_PATH) and zipfile.is_zipfile(ZIP_PATH):
        return
    os.makedirs(RAW_DIR, exist_ok=True)
    print(f"downloading {ZIP_URL} ...", flush=True)
    subprocess.run(
        ["curl", "-sS", "-C", "-", "--retry", "5", "--retry-delay", "5",
         "-A", "Mozilla/5.0 (X11; Linux x86_64)", "-o", ZIP_PATH, ZIP_URL],
        check=True,
    )


def find_member(zf, needle):
    hits = [n for n in zf.namelist() if needle in n and n.lower().endswith(".csv")]
    if len(hits) != 1:
        raise RuntimeError(f"expected exactly 1 member matching {needle!r}, got {hits}")
    return hits[0]


def load_country_codes(zf):
    """Read country codes, add iso3_recode (490 -> TWN), and write the provenance CSV."""
    member = find_member(zf, "country_codes")
    with zf.open(member) as fh:
        cc = pd.read_csv(fh, dtype=str, keep_default_na=False)
    code_col = "country_code"
    iso3_col = "country_iso3"
    if code_col not in cc.columns or iso3_col not in cc.columns:
        raise RuntimeError(f"unexpected country-codes columns: {list(cc.columns)}")
    cc[code_col] = cc[code_col].astype(int)
    # BACI codes Taiwan as 490 "Other Asia, nes"; we force iso3_recode to TWN.
    cc["iso3_recode"] = cc[iso3_col].str.strip()
    cc.loc[cc[code_col] == 490, "iso3_recode"] = "TWN"
    # We tag any residual empty ISO3 with a numeric fallback so the flow is kept, never omitted.
    blank = cc["iso3_recode"].isin(["", "N/A", "NA"])
    cc.loc[blank, "iso3_recode"] = "_" + cc.loc[blank, code_col].astype(str)

    out = os.path.join(PROC_DIR, "baci_country_codes.csv")
    with open(out, "w", newline="") as fh:
        fh.write(PROVENANCE)
        fh.write("# note: iso3_recode = country_iso3 except BACI code 490 "
                 "('Other Asia, nes', i.e. Taiwan) -> TWN; residual blank ISO3 -> '_<code>'\n")
        cc.to_csv(fh, index=False)
    print(f"wrote {out} ({len(cc)} codes)")
    return cc.set_index(code_col)["iso3_recode"].to_dict(), member


def process_year(zf, year, iso3_map, parquet_writer=None):
    """Stream one year's CSV from the zip and yield the (i,j)->sum(v) frame."""
    member = find_member(zf, f"Y{year}_")
    agg_parts = []
    nrows = 0
    with zf.open(member) as raw:
        reader = pd.read_csv(
            io.TextIOWrapper(raw, encoding="utf-8"),
            dtype={"t": "int32", "i": "int32", "j": "int32", "k": str},
            na_values=["NA"],
            skipinitialspace=True,
            chunksize=CHUNKSIZE,
        )
        for chunk in reader:
            chunk["v"] = pd.to_numeric(chunk["v"], errors="coerce")
            nrows += len(chunk)
            agg_parts.append(chunk.groupby(["i", "j"], sort=False)["v"].sum())
            if parquet_writer is not None:
                chunk["q"] = pd.to_numeric(chunk["q"], errors="coerce")
                tbl = pa.Table.from_pandas(
                    chunk[["t", "i", "j", "k", "v", "q"]], preserve_index=False
                ).cast(PARQUET_SCHEMA)
                parquet_writer.write_table(tbl)
    agg = (
        pd.concat(agg_parts).groupby(level=[0, 1]).sum().reset_index()
        .rename(columns={"v": "value_kusd"})
    )
    agg.insert(0, "year", year)
    agg["exporter_iso3"] = agg["i"].map(iso3_map)
    agg["importer_iso3"] = agg["j"].map(iso3_map)
    missing = agg["exporter_iso3"].isna().sum() + agg["importer_iso3"].isna().sum()
    if missing:
        raise RuntimeError(f"{year}: {missing} flows with unmapped country codes")
    print(f"  {year}: {nrows:,} HS6 rows -> {len(agg):,} dyads, "
          f"world total = {agg['value_kusd'].sum() / 1e9:.2f} T USD", flush=True)
    return agg[["year", "exporter_iso3", "importer_iso3", "value_kusd"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep-zip", action="store_true",
                    help="do not delete the raw zip after processing")
    args = ap.parse_args()

    os.makedirs(PROC_DIR, exist_ok=True)
    ensure_zip()

    panel = []
    with zipfile.ZipFile(ZIP_PATH) as zf:
        iso3_map, _ = load_country_codes(zf)
        pq_path = os.path.join(PROC_DIR, f"baci_{PARQUET_YEAR}_hs6.parquet")
        for year in YEARS:
            writer = None
            if year == PARQUET_YEAR:
                writer = pq.ParquetWriter(pq_path, PARQUET_SCHEMA, compression="snappy")
            try:
                panel.append(process_year(zf, year, iso3_map, parquet_writer=writer))
            finally:
                if writer is not None:
                    writer.close()
                    print(f"wrote {pq_path}")

    wtw = pd.concat(panel, ignore_index=True)
    out = os.path.join(PROC_DIR, "wtw_agg_2017_2024.csv")
    with open(out, "w", newline="") as fh:
        fh.write(PROVENANCE)
        fh.write("# unit: value_kusd is THOUSANDS of current USD (BACI native 'v'); "
                 "USD = value_kusd * 1e3\n")
        fh.write("# note: Taiwan = BACI code 490 'Other Asia, nes', recoded to TWN\n")
        wtw.to_csv(fh, index=False)
    print(f"wrote {out} ({len(wtw):,} rows)")

    # ---- sanity checks: we validate the panel before anything downstream reads it ----
    yrs = sorted(wtw["year"].unique())
    assert yrs == YEARS, f"panel years {yrs} != {YEARS}"
    totals = wtw.groupby("year")["value_kusd"].sum() / 1e9  # kUSD -> trillion USD
    print("\nWorld total trade per year (trillion current USD):")
    for y, t in totals.items():
        print(f"  {y}: {t:.2f}")
    assert 15 < totals.loc[2023] < 30, f"2023 world total {totals.loc[2023]:.2f}T out of range"
    twn = wtw[wtw["exporter_iso3"] == "TWN"].groupby("year")["value_kusd"].sum() / 1e9
    print("\nTaiwan (TWN, BACI 490) exports per year (trillion USD):")
    for y, t in twn.items():
        print(f"  {y}: {t:.4f}")
    assert (twn > 0.1).all(), "Taiwan flows implausibly small"

    if not args.keep_zip and os.path.exists(ZIP_PATH):
        os.remove(ZIP_PATH)
        print(f"\ndeleted {ZIP_PATH}")
    print("DONE")


if __name__ == "__main__":
    main()
