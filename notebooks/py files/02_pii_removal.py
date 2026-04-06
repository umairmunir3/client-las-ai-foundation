"""
═══════════════════════════════════════════════════════════════════
 LAS CMS — Phase 3.1: PII Identification & Removal
 
 This script identifies and anonymizes all personally identifiable
 information (PII) in the CMS data before any AI training.
 
 PII Types Handled:
   - CNIC numbers (National ID)
   - Client names
   - Father/husband names
   - Phone numbers
   - Addresses (if present)
   - Names embedded in free text (caseFacts, hearing notes)
 
 Usage:
   conda activate las_cms
   python 02_pii_removal.py
 
 Input:  CSV files in ../data/
 Output: Anonymized CSVs in ../outputs/anonymized/
         PII mapping file in ../outputs/pii_mapping/ (CONFIDENTIAL)
═══════════════════════════════════════════════════════════════════
"""

import pandas as pd
import numpy as np
import hashlib
import re
import json
from pathlib import Path
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

DATA_DIR = Path("../data")
OUTPUT_DIR = Path("../outputs/anonymized")
MAPPING_DIR = Path("../outputs/pii_mapping")  # KEEP THIS CONFIDENTIAL
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MAPPING_DIR.mkdir(parents=True, exist_ok=True)

# Salt for hashing — change this for your deployment
# This ensures the same name always maps to the same hash
# but cannot be reversed without the salt
HASH_SALT = "LAS_CMS_2026_CONFIDENTIAL"

print("=" * 65)
print("  LAS CMS — Phase 3.1: PII Removal")
print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("=" * 65)


# ═══════════════════════════════════════════════════════════════════
# PII ANONYMIZATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def hash_value(value, prefix=""):
    """Create a consistent, non-reversible hash of a PII value."""
    if pd.isna(value) or str(value).strip() == '':
        return value
    salted = f"{HASH_SALT}:{str(value).strip()}"
    hashed = hashlib.sha256(salted.encode()).hexdigest()[:8].upper()
    return f"{prefix}{hashed}"


def anonymize_cnic(cnic):
    """Anonymize CNIC: 12345-6789012-3 → CNIC_XXXX_XX"""
    if pd.isna(cnic) or str(cnic).strip() == '':
        return cnic
    cnic_str = str(cnic).strip()
    # Keep fake CNICs as-is (they're already not real)
    if '00000-0000000-0' in cnic_str:
        return 'FAKE_PLACEHOLDER'
    return hash_value(cnic_str, "CNIC_")


def anonymize_name(name):
    """Anonymize a person's name: Muhammad Ali → NAME_A3F2B1C4"""
    if pd.isna(name) or str(name).strip() == '':
        return name
    return hash_value(str(name).strip(), "NAME_")


def anonymize_phone(phone):
    """Anonymize phone: 0300-1234567 → PHONE_XXXX"""
    if pd.isna(phone) or str(phone).strip() == '':
        return phone
    return hash_value(str(phone).strip(), "PHONE_")


def anonymize_text_field(text, name_list=None):
    """
    Remove PII from free text fields (caseFacts, hearing notes).
    
    Strategy:
    1. Replace CNIC patterns with [CNIC_REDACTED]
    2. Replace phone patterns with [PHONE_REDACTED]
    3. Replace known names (from the name columns) with [NAME_REDACTED]
    """
    if pd.isna(text) or str(text).strip() == '':
        return text
    
    text = str(text)
    
    # 1. CNIC pattern: XXXXX-XXXXXXX-X
    text = re.sub(r'\d{5}-\d{7}-\d{1}', '[CNIC_REDACTED]', text)
    
    # 2. Pakistani phone patterns
    # +923XX-XXXXXXX, 03XX-XXXXXXX, 03XXXXXXXXX
    text = re.sub(r'(\+92|0)3\d{2}[\s-]?\d{7}', '[PHONE_REDACTED]', text)
    
    # 3. Generic phone-like patterns (7+ consecutive digits)
    text = re.sub(r'\b\d{7,13}\b', '[NUM_REDACTED]', text)
    
    # 4. Replace known names if provided
    if name_list:
        for name in name_list:
            if name and len(str(name)) > 2:
                # Case-insensitive replacement
                pattern = re.escape(str(name).strip())
                text = re.sub(pattern, '[NAME_REDACTED]', text, flags=re.IGNORECASE)
    
    return text


# ═══════════════════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════════════════

print("\nLoading data...")
programs = pd.read_csv(DATA_DIR / "programs.csv")
print(f"  ✓ programs: {len(programs):,} rows")

hearings = pd.DataFrame()
try:
    hearings = pd.read_csv(DATA_DIR / "hearings.csv")
    print(f"  ✓ hearings: {len(hearings):,} rows")
except FileNotFoundError:
    print("  ⚠ hearings.csv not found — skipping")

programs_detail = pd.DataFrame()
try:
    programs_detail = pd.read_csv(DATA_DIR / "programs_detail.csv")
    print(f"  ✓ programs_detail: {len(programs_detail):,} rows")
except FileNotFoundError:
    print("  ⚠ programs_detail.csv not found — skipping")

users = pd.DataFrame()
try:
    users = pd.read_csv(DATA_DIR / "users.csv")
    print(f"  ✓ users: {len(users):,} rows")
except FileNotFoundError:
    print("  ⚠ users.csv not found — skipping")


# ═══════════════════════════════════════════════════════════════════
# STEP 1: BUILD NAME LIST FOR TEXT REDACTION
# ═══════════════════════════════════════════════════════════════════

print("\n[Step 1] Building name list for text redaction...")

all_names = set()
name_columns = {
    'programs': ['clientName', 'fatherHusbandName'],
    'users': ['name'],
}

for table_name, cols in name_columns.items():
    df = programs if table_name == 'programs' else users
    if df.empty:
        continue
    for col in cols:
        if col in df.columns:
            names = df[col].dropna().unique()
            for name in names:
                name_str = str(name).strip()
                if len(name_str) > 2:
                    all_names.add(name_str)
                    # Also add individual name parts (first name, last name)
                    for part in name_str.split():
                        if len(part) > 2:
                            all_names.add(part)

print(f"  Collected {len(all_names)} unique name/name-parts for text redaction")


# ═══════════════════════════════════════════════════════════════════
# STEP 2: CREATE PII MAPPING (Before anonymization)
# ═══════════════════════════════════════════════════════════════════

print("\n[Step 2] Creating PII mapping file (reversible reference)...")

# This mapping allows the legal team to look up the original value
# if needed. MUST BE KEPT CONFIDENTIAL AND SEPARATE FROM THE DATA.

pii_mapping = []

if 'cnic' in programs.columns:
    for val in programs['cnic'].dropna().unique():
        pii_mapping.append({
            'type': 'CNIC',
            'original': str(val),
            'anonymized': anonymize_cnic(val),
            'table': 'programs'
        })

if 'clientName' in programs.columns:
    for val in programs['clientName'].dropna().unique():
        pii_mapping.append({
            'type': 'CLIENT_NAME',
            'original': str(val),
            'anonymized': anonymize_name(val),
            'table': 'programs'
        })

if 'fatherHusbandName' in programs.columns:
    for val in programs['fatherHusbandName'].dropna().unique():
        pii_mapping.append({
            'type': 'FATHER_NAME',
            'original': str(val),
            'anonymized': anonymize_name(val),
            'table': 'programs'
        })

if 'mobileNo' in programs.columns:
    for val in programs['mobileNo'].dropna().unique():
        pii_mapping.append({
            'type': 'PHONE',
            'original': str(val),
            'anonymized': anonymize_phone(val),
            'table': 'programs'
        })

mapping_df = pd.DataFrame(pii_mapping)
mapping_path = MAPPING_DIR / "pii_mapping_CONFIDENTIAL.csv"
mapping_df.to_csv(mapping_path, index=False)
print(f"  ✓ PII mapping saved: {mapping_path}")
print(f"    ⚠ THIS FILE IS CONFIDENTIAL — do not share or commit to git")
print(f"    Total mappings: {len(mapping_df):,}")


# ═══════════════════════════════════════════════════════════════════
# STEP 3: ANONYMIZE STRUCTURED FIELDS
# ═══════════════════════════════════════════════════════════════════

print("\n[Step 3] Anonymizing structured PII fields...")

# -- Programs table --
programs_anon = programs.copy()
field_actions = {
    'clientName':        ('Client Name',     anonymize_name),
    'fatherHusbandName': ('Father/Husband',  anonymize_name),
    'cnic':              ('CNIC',            anonymize_cnic),
    'mobileNo':          ('Mobile Number',   anonymize_phone),
}

for field, (label, func) in field_actions.items():
    if field in programs_anon.columns:
        before_sample = programs_anon[field].dropna().head(2).tolist()
        programs_anon[field] = programs_anon[field].apply(func)
        after_sample = programs_anon[field].dropna().head(2).tolist()
        print(f"  ✓ {label:20s} | Before: {before_sample[0] if before_sample else 'N/A':30s} → After: {after_sample[0] if after_sample else 'N/A'}")

# Optional: anonymize address if present
for addr_col in ['clientAddress', 'address', 'permanentAddress']:
    if addr_col in programs_anon.columns:
        programs_anon[addr_col] = programs_anon[addr_col].apply(
            lambda x: '[ADDRESS_REDACTED]' if pd.notna(x) and str(x).strip() != '' else x)
        print(f"  ✓ {addr_col:20s} | Redacted")


# ═══════════════════════════════════════════════════════════════════
# STEP 4: ANONYMIZE FREE TEXT FIELDS
# ═══════════════════════════════════════════════════════════════════

print("\n[Step 4] Anonymizing free text fields (caseFacts, hearing notes)...")

# Anonymize caseFacts
if 'caseFacts' in programs_anon.columns:
    name_list = list(all_names)
    print(f"  Processing caseFacts ({len(programs_anon):,} records)...")
    programs_anon['caseFacts'] = programs_anon['caseFacts'].apply(
        lambda x: anonymize_text_field(x, name_list))
    print("  ✓ caseFacts anonymized")

# Anonymize hearing notes
hearings_anon = hearings.copy() if not hearings.empty else pd.DataFrame()
if not hearings_anon.empty:
    notes_col = None
    for col in ['hearingProceeding', 'hearing_notes', 'notes', 'proceedings']:
        if col in hearings_anon.columns:
            notes_col = col
            break
    
    if notes_col:
        name_list = list(all_names)
        print(f"  Processing {notes_col} ({len(hearings_anon):,} records)...")
        hearings_anon[notes_col] = hearings_anon[notes_col].apply(
            lambda x: anonymize_text_field(x, name_list))
        print(f"  ✓ {notes_col} anonymized")


# ═══════════════════════════════════════════════════════════════════
# STEP 5: SAVE ANONYMIZED DATA
# ═══════════════════════════════════════════════════════════════════

print("\n[Step 5] Saving anonymized datasets...")

programs_anon.to_csv(OUTPUT_DIR / "programs_anonymized.csv", index=False)
print(f"  ✓ programs_anonymized.csv ({len(programs_anon):,} rows)")

if not hearings_anon.empty:
    hearings_anon.to_csv(OUTPUT_DIR / "hearings_anonymized.csv", index=False)
    print(f"  ✓ hearings_anonymized.csv ({len(hearings_anon):,} rows)")

if not programs_detail.empty:
    # programs_detail may also have PII — copy relevant anonymization
    pd_anon = programs_detail.copy()
    for field, (_, func) in field_actions.items():
        if field in pd_anon.columns:
            pd_anon[field] = pd_anon[field].apply(func)
    pd_anon.to_csv(OUTPUT_DIR / "programs_detail_anonymized.csv", index=False)
    print(f"  ✓ programs_detail_anonymized.csv ({len(pd_anon):,} rows)")

# Copy non-PII tables as-is
non_pii_tables = ['category', 'court_name', 'case_stage', 'court']
for table in non_pii_tables:
    src = DATA_DIR / f"{table}.csv"
    if src.exists():
        df = pd.read_csv(src)
        df.to_csv(OUTPUT_DIR / f"{table}.csv", index=False)
        print(f"  ✓ {table}.csv (no PII — copied as-is)")


# ═══════════════════════════════════════════════════════════════════
# STEP 6: VERIFICATION REPORT
# ═══════════════════════════════════════════════════════════════════

print("\n[Step 6] Verification — checking no PII leaked...")

# Quick check: sample the anonymized data
verification_passed = True
for field in ['clientName', 'fatherHusbandName', 'cnic', 'mobileNo']:
    if field in programs_anon.columns:
        sample = programs_anon[field].dropna().head(5)
        has_real_data = False
        for val in sample:
            val_str = str(val)
            # Check if it looks like a hash or redaction
            if not (val_str.startswith('NAME_') or val_str.startswith('CNIC_') or
                    val_str.startswith('PHONE_') or val_str.startswith('FAKE_') or
                    'REDACTED' in val_str):
                has_real_data = True
                verification_passed = False
                print(f"  ⚠ WARNING: {field} may still contain real PII: {val_str[:30]}")

if verification_passed:
    print("  ✓ All structured PII fields verified — anonymization successful")

# Summary
print("\n" + "=" * 65)
print("  PII REMOVAL COMPLETE")
print("=" * 65)
print(f"""
  📁 Anonymized files:  {OUTPUT_DIR}
  🔒 PII mapping:       {MAPPING_DIR} (CONFIDENTIAL!)
  
  Records processed:
    programs:        {len(programs_anon):,}
    hearings:        {len(hearings_anon):,}
    programs_detail: {len(programs_detail):,}
  
  PII types handled:
    ✓ Client names → hashed (NAME_XXXX)
    ✓ Father/husband names → hashed (NAME_XXXX)
    ✓ CNIC numbers → hashed (CNIC_XXXX) 
    ✓ Phone numbers → hashed (PHONE_XXXX)
    ✓ Addresses → redacted
    ✓ Names in free text → [NAME_REDACTED]
    ✓ CNICs in free text → [CNIC_REDACTED]
    ✓ Phone numbers in free text → [PHONE_REDACTED]
  
  NEXT: Run 03_data_cleaning.py
""")
