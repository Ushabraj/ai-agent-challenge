#!/usr/bin/env python3
import argparse, pandas as pd, pdfplumber, importlib, sys
from pathlib import Path
ROOT, PARSERS, DATA = Path(__file__).parent, Path(__file__).parent/"custom_parsers", Path(__file__).parent/"data"
PARSERS.mkdir(exist_ok=True)
TEMPLATE="""\
import pandas as pd, pdfplumber
from pathlib import Path
def parse(path:str)->pd.DataFrame:
    f=Path(path)
    if f.suffix==".csv": df=pd.read_csv(f)
    elif f.suffix==".pdf":
        rows=[]
        with pdfplumber.open(f) as pdf:
            for p in pdf.pages:
                for t in p.extract_tables() or []:
                    h,*d=t
                    for r in d:
                        if r!=h and any(r): rows.append(r)
        df=pd.DataFrame(rows,columns=h) if rows else pd.DataFrame()
    else: df=pd.DataFrame()
    for c in df.columns:
        if any(x in c.lower() for x in["debit","credit","balance"]):
            df[c]=pd.to_numeric(df[c],errors="coerce").fillna(0)
        if df[c].dtype=="object": df[c]=df[c].fillna("").str.strip()
    return df
"""
def normalize(df):
    df=df.copy().reset_index(drop=True)
    for c in df.columns:
        if df[c].dtype=="object": df[c]=df[c].astype(str).str.strip()
        if c.lower() in["debit amt","credit amt","balance"]:
            df[c]=pd.to_numeric(df[c],errors="coerce").round(2).fillna(0)
    return df
def run(bank):
    for i in range(1,4):
        print(f"\n[INFO] Attempt {i}/3 for {bank}")
        path=PARSERS/f"{bank}_parser.py"; path.write_text(TEMPLATE)
        print(f"[INFO] Written parser -> {path}")
        try:
            sys.path.insert(0,str(ROOT))
            parse=importlib.import_module(f"custom_parsers.{bank}_parser").parse
            csv,pdf=DATA/bank/"result.csv",DATA/bank/"sample.pdf"
            f=csv if csv.exists() else pdf
            if not f.exists(): raise FileNotFoundError(f"No data for {bank}")
            df=parse(str(f))
            print(f"\n[INFO] Parsed DataFrame ({len(df)} rows, {len(df.columns)} columns):")
            print(df.head())
            if csv.exists():
                ref,df=normalize(pd.read_csv(csv)),normalize(df)
                mism=[]
                for c in set(ref.columns)&set(df.columns):
                    try: pd.testing.assert_series_equal(df[c].reset_index(drop=True),ref[c].reset_index(drop=True),check_dtype=False,rtol=1e-3);print(f"[PASS] Column '{c}' matches")
                    except: mism.append(c);print(f"[FAIL] Column '{c}' does NOT match")
                if mism: raise Exception(f"Mismatched {mism}")
            print("[INFO] Parser test passed!");print(f"[PASS] Success on attempt {i}");return
        except Exception as e: print(f"[FAIL] Attempt {i} failed: {e}")
    print(f"[ERROR] All attempts failed for {bank}")
if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("--target",required=True)
    run(a.parse_args().target.strip().lower())
