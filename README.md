give the readme to this after adding the stream lit

# Bank Statement Parser Agent

This project is an **AI-powered agent** that parses bank statements (PDF/CSV) into structured pandas DataFrames, validates them against reference data, and automatically fixes mismatches by regenerating parser code (up to 3 attempts).

Features

--Parse CSV and PDF bank statements.

--Validate against a reference CSV.

--Supports multiple banks: ICICI, SBI, HDFC, AXIS, KOTAK, or All Banks.

--Automatically retries parsing up to 3 attempts if mismatches are detected.

--Streamlit interface allows interactive validation and viewing all rows/column

##  5-Step Run Instructions

1. **Clone the repository**  
   ```bash
   git clone <repo-url>
   cd agent-challenge
   ```

2. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

3. **Add your bank data**  
   Place sample bank statement files in the `data/<bank>/` folder.  
   Example for ICICI:  
   ```
   data/icici/sample.pdf
   data/icici/result.csv
   ```

4. **Run the agent**  
   ```bash
   python agent.py --target icici
   ```

5. **Check results**  
   - If parsing is correct →  Success  
   - If mismatched → Agent retries up to 3 attempts  
   - If still failing →  Check parser/data

---

##  Agent Workflow Diagram

The agent follows this flow:

![Agent Workflow]
[ Start ]
   ↓
User runs: python agent.py --target icici
   ↓
[ Backup old parser ]
   ↓
[ Write new parser in custom_parsers/ ]
   ↓
[ Run pytest tests ]
   ↓
[ Compare output.csv with result.csv ]
   ├── If Match → Success
   └── If Mismatch → Retry (up to 3 attempts)
                        ↓
                  Failure after 3 attempts


**Run Streamlit Validator** 

streamlit run app.py                  



## How It Works

The agent works in a loop of up to 3 attempts:  
1. **Backup** the existing parser.  
2. **Write** a new parser (default or AI-generated).  
3. **Test** the parser using reference data (`result.csv`).  
4. **Compare** parsed output with reference.  
5. If mismatched, retry with improvements.  
   -  If matches → Success  
   -  If still fails after 3 attempts → Manual debugging required  

This design ensures **self-healing automation**, reducing manual parser adjustments for each new bank statement format.
my readme is this plzz edit this and give

**NOTE**
**Add API Key**
If your parser or AI-assisted agent requires an API key:
**set API_KEY="your_api_key_here"**
