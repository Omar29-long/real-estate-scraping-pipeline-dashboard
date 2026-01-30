from __future__ import annotations

from src.clean_data import clean_raw_csv
from src.analyse_data import enrich_and_analyse

if __name__ == "__main__":
    df_clean, report = clean_raw_csv()
    print(report)
    art = enrich_and_analyse()
    print("Ready parquet écrit.")
