import pandas as pd
from custom_parsers.icici_parser import parse
from pathlib import Path

EXPECTED_COLUMNS = ["Date", "Description", "Debit Amt", "Credit Amt", "Balance"]

def test_parser():
    bank_folder = Path("data/icici")
    csv_path = bank_folder / "result.csv"
    pdf_path = bank_folder / "sample.pdf"
    file_to_parse = csv_path if csv_path.exists() else pdf_path
    df = parse(str(file_to_parse))
    print("\nParsed DataFrame (first 5 rows):")
    print(df.head())
    missing_cols = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise AssertionError(f"❌ Missing columns: {missing_cols}")
    print("\n✅ Test passed! Columns matched.")

if __name__ == "__main__":
    test_parser()
