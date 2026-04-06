# LAS CMS Data Analysis & AI Preparation Pipeline

**Project:** Legal Aid Society (LAS) Pakistan — CMS Data  

---

## What This Does

Takes the raw CMS MySQL database and transforms it into clean, anonymized,
RAG-ready data that a lawyer can query using AI.

```
Raw MySQL Database (WSL)
    │
    ▼ Step 1: Export to CSV
    │   → 20+ tables exported as CSV files
    │
    ▼ Step 2: Exploratory Data Analysis (Python)
    │   → 18+ charts, findings report, AI readiness score
    │
    ▼ Step 3.1: PII Removal
    │   → Names, CNICs, phones anonymized
    │   → Free text redacted
    │
    ▼ Step 3.2: Data Cleaning (8 tasks)
    │   → Court spellings fixed, dates parsed
    │   → Outcomes standardized, duplicates removed
    │
    ▼ Step 3.3: RAG Preparation
        → Case narratives generated
        → Chunked documents with metadata
        → JSONL ready for vector store
```

---

## Quick Start — Step by Step

### STEP 1: Export Data from MySQL (in WSL)

```bash
# Open WSL terminal
cd /path/to/las_cms_analysis/scripts/

# Edit the script first — update MYSQL_PASS
nano export_cms_to_csv.sh

# Make executable and run
chmod +x export_cms_to_csv.sh
./export_cms_to_csv.sh
```

This creates `LAS_CMS_Data/` on your Windows Desktop with all CSV files.

### STEP 2: Set Up Conda Environment (in Windows)

```bash
# Open Anaconda Prompt (NOT regular CMD)
cd E:\devgate\Legal_AI_Society\LAS_CMS_Analysis

# Run setup
setup_environment.bat
```

This creates the `las_cms` conda environment with all dependencies.

### STEP 3: Copy CSV Files

Copy the CSV files from `Desktop\LAS_CMS_Data\` into the `data\` folder:

```
LAS_CMS_Analysis/
├── data/              ← PUT CSV FILES HERE
│   ├── programs.csv
│   ├── hearings.csv
│   ├── programs_detail.csv
│   └── ...
├── notebooks/
├── outputs/
└── ...
```

### STEP 4: Run the Analysis Pipeline

```bash
# Activate environment
conda activate las_cms

# Navigate to notebooks
cd notebooks

# Run in order:
python 01_eda_analysis.py          # Phase 2: Charts + findings
python 02_pii_removal.py           # Phase 3.1: Anonymize PII
python 03_data_cleaning.py         # Phase 3.2: Clean data
python 04_rag_preparation.py       # Phase 3.3: Prepare for RAG
```

### STEP 5: Check Results

All outputs are in the `outputs/` folder:

```
outputs/
├── chart_01_case_decisions.png
├── chart_02_case_status.png
├── ...
├── chart_18_ai_readiness_score.png
├── phase2_summary_report.txt
├── findings.json
├── pii_inventory.csv
├── anonymized/
│   ├── programs_anonymized.csv
│   └── hearings_anonymized.csv
├── cleaned/
│   ├── programs_cleaned.csv
│   └── hearings_cleaned.csv
├── rag_ready/
│   ├── cms_cases_rag.jsonl       ← FEED THIS TO VECTOR STORE
│   ├── cms_cases_rag.json
│   ├── cms_metadata.csv
│   └── RAG_INTEGRATION_GUIDE.txt
└── pii_mapping/
    └── pii_mapping_CONFIDENTIAL.csv  ← KEEP THIS SECURE!
```

---

## Project Structure

```
LAS_CMS_Analysis/
│
├── README.md                    ← You are here
├── environment.yml              ← Conda environment specification
├── setup_environment.bat        ← Windows setup script
│
├── scripts/
│   └── export_cms_to_csv.sh     ← WSL MySQL → CSV export
│
├── data/                        ← Raw CSV files (from export)
│   └── (put CSV files here)
│
├── notebooks/
│   ├── 01_eda_analysis.py       ← Phase 2: Full EDA with charts
│   ├── 02_pii_removal.py        ← Phase 3.1: PII anonymization
│   ├── 03_data_cleaning.py      ← Phase 3.2: Data cleaning
│   └── 04_rag_preparation.py    ← Phase 3.3: RAG preparation
│
└── outputs/                     ← All generated outputs
    ├── (charts, reports)
    ├── anonymized/
    ├── cleaned/
    ├── rag_ready/
    └── pii_mapping/
```

---

## Important Notes

1. **PII Mapping File** — The file at `outputs/pii_mapping/pii_mapping_CONFIDENTIAL.csv`
   contains the mapping between real names/CNICs and their hashed versions.
   This file MUST be kept confidential and NEVER committed to git.

2. **Data is Real** — Even after anonymization, the case facts and hearing
   notes may contain identifiable information in free text. Treat all
   output files as confidential.

3. **Git Ignore** — Add these to `.gitignore`:
   ```
   data/
   outputs/pii_mapping/
   outputs/anonymized/
   ```

4. **Re-running** — Scripts are safe to re-run. They overwrite previous outputs.

---

## Requirements

- Windows 10/11 with WSL (Ubuntu)
- MySQL running in WSL with `laoorgpk_cmslaravel` database
- Anaconda/Miniconda installed on Windows
- ~500MB free disk space
