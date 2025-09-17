import streamlit as st
import pandas as pd
import tabula  # For PDF parsing
import os

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="📊 Bank Statement Validator",
    layout="wide",
    page_icon="💳"
)

# ---------------- Sidebar ----------------
st.sidebar.title("Bank Statement Validator")
st.sidebar.markdown("""
**Instructions:**
1. Upload your **Bank Statement** (CSV or PDF).
2. Upload the **Reference CSV**.
3. Select the **Bank** you want to validate.
4. Click **Validate** to check for mismatches.
""")

# ---------------- Title & Description ----------------
st.title("💳 AI-Powered Bank Statement Validator")
st.markdown("""
This app validates your **uploaded bank statement** against a **reference CSV**.  
It supports both **CSV** and **PDF** files and highlights if your data **matches** or **does not match**.  
All rows and columns are displayed for inspection.
""")

# ---------------- Bank Selection ----------------
bank_options = ["All Banks", "ICICI", "HDFC", "SBI", "AXIS", "KOTAK"]
selected_bank = st.sidebar.selectbox("Select Bank to Validate", bank_options)

# ---------------- Upload Files ----------------
uploaded_file = st.file_uploader("Upload Bank Statement (CSV or PDF)", type=["csv", "pdf"])
reference_file = st.file_uploader("Upload Reference CSV", type=["csv"])

# ---------------- Parser Functions ----------------
def parse_file(file, bank=None):
    """Parse CSV or PDF file into a DataFrame"""
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    elif file.name.endswith(".pdf"):
        dfs = tabula.read_pdf(file, pages='all', multiple_tables=True)
        if len(dfs) == 0:
            raise ValueError("No tables found in PDF")
        df = pd.concat(dfs, ignore_index=True)
    else:
        raise ValueError("Unsupported file type")
    
    # Filter by selected bank
    if bank and bank != "All Banks" and "Bank" in df.columns:
        df = df[df["Bank"].str.upper() == bank.upper()]
    
    return df

def validate_dataframe(parsed_df, reference_df):
    """Check if rows and columns match exactly"""
    if list(parsed_df.columns) != list(reference_df.columns):
        return False
    return parsed_df.reset_index(drop=True).equals(reference_df.reset_index(drop=True))

# ---------------- Parse & Validate ----------------
if uploaded_file and reference_file:
    if st.button(" Validate Statement"):
        with st.spinner("Parsing and validating your statement... ⏳"):
            try:
                parsed_df = parse_file(uploaded_file, bank=selected_bank)
                reference_df = pd.read_csv(reference_file)

                # Validation
                matched = validate_dataframe(parsed_df, reference_df)

                # ---------------- Result ----------------
                st.subheader(" Validation Result")
                if matched:
                    st.success(f" Uploaded statement matches the reference for {selected_bank}!")
                else:
                    st.error(f" Uploaded statement does NOT match the reference for {selected_bank}!")

                # ---------------- Parsed Table ----------------
                st.subheader("Parsed Bank Statement")
                st.dataframe(parsed_df, use_container_width=True)
                
                st.markdown(f"**Number of rows:** {parsed_df.shape[0]}")
                st.markdown(f"**Number of columns:** {parsed_df.shape[1]}")
                st.markdown(f"**Columns:** {', '.join(parsed_df.columns)}")

                if not matched:
                    st.info(" Hint: Compare the parsed table with the reference to identify mismatches.")

            except Exception as e:
                st.error(f" Error parsing or validating files: {e}")

else:
    st.info("📥 Please upload both a bank statement and reference CSV to start validation.")
