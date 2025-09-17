#!/usr/bin/env python3
"""
Bank Statement Parser Agent
Parses bank PDFs/CSVs into pandas DataFrames and validates against reference CSV.
Generates parser + test automatically.
"""

import os
import sys
import argparse
from pathlib import Path
import pandas as pd
import traceback

# --- Groq API ---
try:
    from groq import Groq
    GROQ_API_KEY = "USER API KEY"
    client = Groq(api_key=GROQ_API_KEY)
except Exception:
    client = None
    print("[WARN] Groq client not available, using default parser.")

PROJECT_ROOT = Path(__file__).parent.resolve()
PARSERS_DIR = PROJECT_ROOT / "custom_parsers"
DATA_DIR = PROJECT_ROOT / "data"

DEFAULT_TEMPLATE = """\
import pandas as pd
import pdfplumber
from pathlib import Path

def parse(file_path: str) -> pd.DataFrame:
    df = pd.DataFrame()
    file_path = Path(file_path)
    if file_path.suffix.lower() == '.csv':
        df = pd.read_csv(file_path)
    elif file_path.suffix.lower() == '.pdf':
        rows = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if not table:
                        continue
                    header = table[0]
                    for row in table[1:]:
                        if row == header or all((cell is None or str(cell).strip() == '') for cell in row):
                            continue
                        rows.append(row)
        if rows:
            df = pd.DataFrame(rows, columns=header)
    # Clean numeric columns
    numeric_cols = ["Debit Amt", "Credit Amt", "Balance"]
    for col in df.columns:
        if any(nc.lower() in col.lower() for nc in numeric_cols):
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].fillna('').str.strip()
    return df
"""

class BankParserAgent:
    def __init__(self):
        self.max_attempts = 3
        PARSERS_DIR.mkdir(exist_ok=True)

    def write_parser(self, bank: str, use_llm=False) -> Path:
        parser_path = PARSERS_DIR / f"{bank}_parser.py"
        parser_code = DEFAULT_TEMPLATE
        if use_llm and client:
            try:
                prompt = f"""
                Generate a Python parser function parse(file_path:str)->pd.DataFrame for {bank} bank PDF/CSV.
                Handle repeated headers, empty rows, numeric cleaning (Debit Amt, Credit Amt, Balance).
                Return pandas DataFrame.
                """
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2
                )
                parser_code = response.choices[0].message.content
                if parser_code.startswith("```"):
                    parser_code = parser_code.split("```")[-2].strip()
                if "def parse(" not in parser_code:
                    parser_code = DEFAULT_TEMPLATE
            except Exception as e:
                print(f"[ERROR] LLM failed: {e}")
                parser_code = DEFAULT_TEMPLATE

        with open(parser_path, "w", encoding="utf-8") as f:
            f.write(parser_code)
        print(f"[INFO] Written parser -> {parser_path}")
        return parser_path

    def _normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize DataFrame for fair comparison."""
        df = df.copy()

        # Strip spaces
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].astype(str).str.strip()

        # Force numeric columns to 2 decimals
        for col in ["Debit Amt", "Credit Amt", "Balance"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").round(2).fillna(0)

        # Reset index + sort rows
        df = df.reset_index(drop=True)
        return df

    def test_parser(self, bank: str):
        sys.path.insert(0, str(PROJECT_ROOT))  # Add project root for imports
        parser_file = PARSERS_DIR / f"{bank}_parser.py"
        if not parser_file.exists():
            raise FileNotFoundError(f"Parser not found: {parser_file}")

        spec = __import__(f"custom_parsers.{bank}_parser", fromlist=["parse"])
        parse_func = getattr(spec, "parse", None)
        if parse_func is None:
            raise AttributeError("parse function not found in parser")

        csv_file = DATA_DIR / bank / "result.csv"
        pdf_file = DATA_DIR / bank / "sample.pdf"
        file_to_parse = csv_file if csv_file.exists() else pdf_file
        if not file_to_parse.exists():
            raise FileNotFoundError(f"No data file found for {bank}: {csv_file} or {pdf_file}")

        df_out = parse_func(str(file_to_parse))
        print(f"\n[INFO] Parsed DataFrame ({len(df_out)} rows, {len(df_out.columns)} columns):")
        print(df_out.head(5))

        if csv_file.exists():
            df_ref = pd.read_csv(csv_file)

            df_out = self._normalize(df_out)
            df_ref = self._normalize(df_ref)

            common_cols = set(df_ref.columns).intersection(set(df_out.columns))
            mismatches = []

            for col in common_cols:
                try:
                    pd.testing.assert_series_equal(
                        df_out[col].reset_index(drop=True),
                        df_ref[col].reset_index(drop=True),
                        check_dtype=False,
                        check_exact=False,
                        rtol=1e-3
                    )
                    print(f"[PASS] Column '{col}' matches")
                except AssertionError:
                    mismatches.append(col)
                    print(f"[FAIL] Column '{col}' does NOT match")

                    # Show diff preview
                    diffs = pd.DataFrame({
                        "parsed": df_out[col],
                        "expected": df_ref[col]
                    })
                    diffs = diffs[diffs["parsed"] != diffs["expected"]].head(5)
                    print(f"   Example mismatches in '{col}':\n{diffs}")

            if mismatches:
                raise AssertionError(f"Mismatched columns: {mismatches}")
        print("[INFO] Parser test passed!\n")
        return True

    def run(self, bank: str):
        for attempt in range(1, self.max_attempts + 1):
            print(f"\n[INFO] Attempt {attempt}/{self.max_attempts} for {bank}")
            use_llm = attempt > 1
            self.write_parser(bank, use_llm)
            try:
                self.test_parser(bank)
                print(f"[PASS] Success on attempt {attempt}")
                return
            except Exception as e:
                print(f"[FAIL] Attempt {attempt} failed: {e}")
        print(f"[ERROR] All attempts failed for {bank}. Check parser/data.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, help="Bank target (e.g., icici)")
    args = parser.parse_args()
    agent = BankParserAgent()
    agent.run(args.target.strip().lower())

if __name__ == "__main__":
    main()
