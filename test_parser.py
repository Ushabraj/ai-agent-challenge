"""
Auto-generated test for icici parser.
"""
from custom_parsers.icici_parser import parse

EXPECTED_COLUMNS = ["Date", "Description", "Debit Amt", "Credit Amt", "Balance"]

def test_parser():
    df = parse()
    print("\nParsed DataFrame (first 5 rows):")
    print(df.head())
    missing_cols = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise AssertionError(f"❌ Missing columns: {missing_cols}")
    print("\n✅ Test passed! Columns matched.")

if __name__ == "__main__":
    test_parser()
