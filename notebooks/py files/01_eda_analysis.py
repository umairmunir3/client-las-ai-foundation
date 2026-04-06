"""
═══════════════════════════════════════════════════════════════════
 LAS CMS — Complete Data Analysis (Phase 2 Redo in Python)
 
 This script reproduces all 35 SQL queries from Phase 2 as Python
 code using pandas, and generates publication-quality charts.
 
 Usage:
   conda activate las_cms
   python 01_eda_analysis.py
   
 Input:  CSV files in ../data/ folder
 Output: Charts (PNG) + summary report in ../outputs/ folder
═══════════════════════════════════════════════════════════════════
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from pathlib import Path
from datetime import datetime
import warnings
import json

warnings.filterwarnings('ignore')

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

# Update this path to where your CSV files are
DATA_DIR = Path("../data")          # Default: parent folder's data/
OUTPUT_DIR = Path("../outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# Chart styling — professional LAS theme
COLORS = {
    'primary':   '#1B4F72',   # Dark blue
    'secondary': '#2E86C1',   # Medium blue
    'accent':    '#17A589',   # Teal
    'warning':   '#E74C3C',   # Red
    'success':   '#27AE60',   # Green
    'neutral':   '#95A5A6',   # Gray
    'bg':        '#FAFBFC',   # Light background
}

PALETTE = ['#1B4F72', '#2E86C1', '#17A589', '#E67E22', '#8E44AD',
           '#E74C3C', '#27AE60', '#F39C12', '#3498DB', '#1ABC9C']

plt.rcParams.update({
    'figure.facecolor': COLORS['bg'],
    'axes.facecolor': '#FFFFFF',
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.titlesize': 14,
    'axes.titleweight': 'bold',
    'figure.titlesize': 16,
    'figure.titleweight': 'bold',
    'axes.grid': True,
    'grid.alpha': 0.3,
    'axes.spines.top': False,
    'axes.spines.right': False,
})

# Summary collector — we'll append findings as we go
findings = []
chart_count = 0


def save_chart(fig, name):
    """Save chart and increment counter."""
    global chart_count
    chart_count += 1
    filepath = OUTPUT_DIR / f"chart_{chart_count:02d}_{name}.png"
    fig.savefig(filepath, dpi=150, bbox_inches='tight', facecolor=COLORS['bg'])
    plt.close(fig)
    print(f"  ✓ Saved: {filepath.name}")
    return filepath


def add_finding(category, finding, severity="INFO"):
    """Add a finding to the summary."""
    findings.append({
        'category': category,
        'finding': finding,
        'severity': severity  # CRITICAL, MODERATE, INFO
    })


# ═══════════════════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════════════════

print("=" * 65)
print("  LAS CMS — Phase 2 Data Analysis (Python)")
print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("=" * 65)
print()

# Load core tables
print("Loading CSV files...")
try:
    programs = pd.read_csv(DATA_DIR / "programs.csv")
    print(f"  ✓ programs:        {len(programs):>6,} rows, {len(programs.columns)} columns")
except FileNotFoundError:
    print("  ✗ ERROR: programs.csv not found!")
    print(f"    Expected location: {(DATA_DIR / 'programs.csv').resolve()}")
    print(f"    Please ensure CSV files are in: {DATA_DIR.resolve()}")
    exit(1)

try:
    hearings = pd.read_csv(DATA_DIR / "hearings.csv")
    print(f"  ✓ hearings:        {len(hearings):>6,} rows, {len(hearings.columns)} columns")
except FileNotFoundError:
    hearings = pd.DataFrame()
    print("  ⚠ hearings.csv not found — skipping hearing analysis")

try:
    programs_detail = pd.read_csv(DATA_DIR / "programs_detail.csv")
    print(f"  ✓ programs_detail: {len(programs_detail):>6,} rows, {len(programs_detail.columns)} columns")
except FileNotFoundError:
    programs_detail = pd.DataFrame()
    print("  ⚠ programs_detail.csv not found — skipping")

try:
    users = pd.read_csv(DATA_DIR / "users.csv")
    print(f"  ✓ users:           {len(users):>6,} rows, {len(users.columns)} columns")
except FileNotFoundError:
    users = pd.DataFrame()
    print("  ⚠ users.csv not found — skipping")

try:
    case_documents = pd.read_csv(DATA_DIR / "case_documents.csv")
    print(f"  ✓ case_documents:  {len(case_documents):>6,} rows, {len(case_documents.columns)} columns")
except FileNotFoundError:
    case_documents = pd.DataFrame()
    print("  ⚠ case_documents.csv not found — skipping")

try:
    court = pd.read_csv(DATA_DIR / "court.csv")
    print(f"  ✓ court:           {len(court):>6,} rows, {len(court.columns)} columns")
except FileNotFoundError:
    court = pd.DataFrame()
    print("  ⚠ court.csv not found — skipping")

try:
    interviews = pd.read_csv(DATA_DIR / "interviews.csv")
    print(f"  ✓ interviews:      {len(interviews):>6,} rows, {len(interviews.columns)} columns")
except FileNotFoundError:
    interviews = pd.DataFrame()
    print("  ⚠ interviews.csv not found — skipping")

try:
    category = pd.read_csv(DATA_DIR / "category.csv")
    print(f"  ✓ category:        {len(category):>6,} rows, {len(category.columns)} columns")
except FileNotFoundError:
    category = pd.DataFrame()


# ═══════════════════════════════════════════════════════════════════
# BATCH 1: CASE OVERVIEW & DISTRIBUTIONS
# ═══════════════════════════════════════════════════════════════════

print("\n" + "─" * 65)
print("BATCH 1: Case Overview & Distributions")
print("─" * 65)

# ── 1.1 Case Decision Breakdown ──────────────────────────────────
print("\n[1.1] Case Decision Breakdown")
if 'caseDecision' in programs.columns:
    decision_counts = programs['caseDecision'].fillna('NOT RECORDED').value_counts()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(decision_counts.index, decision_counts.values, color=PALETTE[:len(decision_counts)])
    ax.set_xlabel('Number of Cases')
    ax.set_title('Case Decision Distribution')
    for bar, val in zip(bars, decision_counts.values):
        ax.text(bar.get_width() + 10, bar.get_y() + bar.get_height()/2,
                f'{val} ({val/len(programs)*100:.1f}%)', va='center', fontsize=10)
    plt.tight_layout()
    save_chart(fig, "case_decisions")
    
    missing_pct = (programs['caseDecision'].isna().sum() / len(programs)) * 100
    add_finding("Outcomes", f"{missing_pct:.1f}% of cases have no decision recorded",
                "CRITICAL" if missing_pct > 10 else "MODERATE")
    print(f"  Missing decisions: {missing_pct:.1f}%")
else:
    print("  ⚠ caseDecision column not found")

# ── 1.2 Case Status Breakdown ────────────────────────────────────
print("\n[1.2] Case Status Breakdown")
if 'currentCaseStatus' in programs.columns:
    status_counts = programs['currentCaseStatus'].fillna('NOT RECORDED').value_counts()
    
    fig, ax = plt.subplots(figsize=(8, 6))
    colors_status = [COLORS['success'] if 'Disposed' in str(s) else 
                     COLORS['warning'] if 'Pending' in str(s) else
                     COLORS['neutral'] for s in status_counts.index]
    wedges, texts, autotexts = ax.pie(status_counts.values, labels=status_counts.index,
                                       autopct='%1.1f%%', colors=colors_status,
                                       startangle=90, textprops={'fontsize': 10})
    ax.set_title('Current Case Status Distribution')
    plt.tight_layout()
    save_chart(fig, "case_status")
    print(f"  Statuses found: {len(status_counts)}")

# ── 1.3 Cases by Year ────────────────────────────────────────────
print("\n[1.3] Cases by Year (Growth Trend)")
date_col = None
for col in ['interviewDate', 'interview_date', 'created_at', 'caseFilingDate']:
    if col in programs.columns:
        date_col = col
        break

if date_col:
    programs['_parsed_date'] = pd.to_datetime(programs[date_col], errors='coerce')
    programs['_year'] = programs['_parsed_date'].dt.year
    yearly = programs['_year'].dropna().astype(int).value_counts().sort_index()
    yearly = yearly[yearly.index >= 2018]  # Filter reasonable years
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(yearly.index.astype(str), yearly.values, color=COLORS['primary'], width=0.6)
    ax.set_xlabel('Year')
    ax.set_ylabel('Number of Cases')
    ax.set_title('Case Volume by Year')
    for bar, val in zip(bars, yearly.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                str(val), ha='center', va='bottom', fontweight='bold')
    # Growth annotation
    if len(yearly) >= 2:
        first_yr, last_yr = yearly.iloc[0], yearly.iloc[-2] if len(yearly) > 2 else yearly.iloc[-1]
        if first_yr > 0:
            growth = ((last_yr - first_yr) / first_yr) * 100
            ax.annotate(f'Growth: {growth:.0f}%', xy=(0.95, 0.95), xycoords='axes fraction',
                       ha='right', va='top', fontsize=12, fontweight='bold',
                       color=COLORS['success'], bbox=dict(boxstyle='round,pad=0.3',
                       facecolor='white', edgecolor=COLORS['success']))
    plt.tight_layout()
    save_chart(fig, "cases_by_year")
    add_finding("Volume", f"Case volume trend: {yearly.to_dict()}", "INFO")
else:
    print("  ⚠ No date column found for year analysis")

# ── 1.4 Gender Breakdown ─────────────────────────────────────────
print("\n[1.4] Gender Breakdown")
if 'gender' in programs.columns:
    gender_counts = programs['gender'].fillna('NOT RECORDED').value_counts()
    
    fig, ax = plt.subplots(figsize=(8, 5))
    colors_gender = [COLORS['secondary'] if 'Female' in str(g) or 'female' in str(g) else 
                     COLORS['primary'] if 'Male' in str(g) or 'male' in str(g) else 
                     COLORS['neutral'] for g in gender_counts.index]
    ax.bar(gender_counts.index, gender_counts.values, color=colors_gender, width=0.5)
    ax.set_ylabel('Number of Cases')
    ax.set_title('Cases by Gender')
    for i, (g, v) in enumerate(gender_counts.items()):
        ax.text(i, v + 10, f'{v}\n({v/len(programs)*100:.1f}%)', ha='center', fontweight='bold')
    plt.tight_layout()
    save_chart(fig, "gender_breakdown")
    
    female_pct = 0
    for g, v in gender_counts.items():
        if 'female' in str(g).lower():
            female_pct += v
    female_pct = (female_pct / len(programs)) * 100
    add_finding("Demographics", f"Female clients: {female_pct:.1f}% of all cases", "INFO")

# ── 1.5 Top 10 Districts ─────────────────────────────────────────
print("\n[1.5] Top 10 Districts")
if 'districtName' in programs.columns:
    district_counts = programs['districtName'].fillna('UNKNOWN').value_counts().head(10)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(district_counts.index[::-1], district_counts.values[::-1], 
                   color=PALETTE[:len(district_counts)])
    ax.set_xlabel('Number of Cases')
    ax.set_title('Top 10 Districts by Case Volume')
    for bar, val in zip(bars, district_counts.values[::-1]):
        ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2,
                str(val), va='center', fontweight='bold')
    plt.tight_layout()
    save_chart(fig, "top_districts")

# ── 1.6 Nature of Case ───────────────────────────────────────────
print("\n[1.6] Nature of Case Breakdown")
if 'natureOfCase' in programs.columns:
    nature_counts = programs['natureOfCase'].fillna('NOT RECORDED').value_counts()
    
    fig, ax = plt.subplots(figsize=(12, 7))
    top_n = min(15, len(nature_counts))
    data = nature_counts.head(top_n)
    bars = ax.barh(data.index[::-1], data.values[::-1], color=COLORS['secondary'], alpha=0.85)
    ax.set_xlabel('Number of Cases')
    ax.set_title(f'Case Types (Top {top_n})')
    for bar, val in zip(bars, data.values[::-1]):
        ax.text(bar.get_width() + 3, bar.get_y() + bar.get_height()/2,
                f'{val} ({val/len(programs)*100:.1f}%)', va='center', fontsize=9)
    plt.tight_layout()
    save_chart(fig, "nature_of_case")


# ═══════════════════════════════════════════════════════════════════
# BATCH 2: FIELD COMPLETENESS AUDIT
# ═══════════════════════════════════════════════════════════════════

print("\n" + "─" * 65)
print("BATCH 2: Field Completeness Audit")
print("─" * 65)

# ── 2.1 Field-by-field completeness check ────────────────────────
print("\n[2.1] Field Completeness Score Card")

# Key fields to check in programs table
key_fields = {
    'clientName':         'Client Name',
    'fatherHusbandName':  'Father/Husband Name', 
    'cnic':               'CNIC Number',
    'gender':             'Gender',
    'age':                'Age',
    'mobileNo':           'Mobile Number',
    'districtName':       'District',
    'natureOfCase':       'Nature of Case',
    'caseFacts':          'Case Facts (Text)',
    'caseDecision':       'Case Decision',
    'currentCaseStatus':  'Case Status',
    'caseFilingDate':     'Case Filing Date',
    'lawyerName':         'Lawyer Name',
    'courtLevel':         'Court Level',
    'programName':        'Program Name',
}

completeness_data = []
for field, label in key_fields.items():
    if field in programs.columns:
        total = len(programs)
        filled = programs[field].notna().sum()
        # Also check for empty strings and placeholder values
        non_empty = programs[field].dropna()
        if non_empty.dtype == 'object':
            non_empty = non_empty[non_empty.str.strip() != '']
            # Check for fake/placeholder values
            if field == 'cnic':
                non_empty = non_empty[~non_empty.str.contains('00000-0000000-0', na=False)]
        
        real_filled = len(non_empty)
        pct = (real_filled / total) * 100
        completeness_data.append({
            'field': label,
            'filled': real_filled,
            'total': total,
            'pct': pct,
            'status': '🟢' if pct >= 90 else '🟡' if pct >= 70 else '🔴'
        })

completeness_df = pd.DataFrame(completeness_data).sort_values('pct', ascending=True)

# Chart
fig, ax = plt.subplots(figsize=(12, 8))
colors_comp = [COLORS['success'] if r['pct'] >= 90 else 
               COLORS['warning'] if r['pct'] >= 70 else
               COLORS['warning'] if r['pct'] >= 50 else
               '#E74C3C' for _, r in completeness_df.iterrows()]

bars = ax.barh(completeness_df['field'], completeness_df['pct'], color=colors_comp)
ax.set_xlabel('Completeness (%)')
ax.set_title('Field Completeness Score Card — programs Table')
ax.set_xlim(0, 110)
ax.axvline(x=90, color=COLORS['success'], linestyle='--', alpha=0.5, label='90% threshold')
ax.axvline(x=70, color='#E67E22', linestyle='--', alpha=0.5, label='70% threshold')

for bar, pct in zip(bars, completeness_df['pct']):
    ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
            f'{pct:.1f}%', va='center', fontsize=10, fontweight='bold')
ax.legend(loc='lower right')
plt.tight_layout()
save_chart(fig, "field_completeness")

# Log critical fields
for _, row in completeness_df.iterrows():
    if row['pct'] < 70:
        add_finding("Completeness", 
                    f"{row['field']}: only {row['pct']:.1f}% complete ({row['filled']}/{row['total']})",
                    "CRITICAL")
    elif row['pct'] < 90:
        add_finding("Completeness",
                    f"{row['field']}: {row['pct']:.1f}% complete", "MODERATE")


# ── 2.2 CNIC Integrity Check ─────────────────────────────────────
print("\n[2.2] CNIC Integrity Analysis")
if 'cnic' in programs.columns:
    cnic_data = programs['cnic'].fillna('')
    
    total_cnics = len(cnic_data)
    null_cnics = (cnic_data == '').sum()
    fake_cnics = cnic_data.str.contains('00000-0000000-0', na=False).sum()
    
    # Check CNIC format: XXXXX-XXXXXXX-X
    valid_format = cnic_data.str.match(r'^\d{5}-\d{7}-\d{1}$', na=False)
    valid_real = valid_format & ~cnic_data.str.contains('00000-0000000-0', na=False)
    
    cnic_breakdown = {
        'Valid & Real': valid_real.sum(),
        'Fake Placeholder\n(00000-0000000-0)': fake_cnics,
        'Invalid Format': (~valid_format & (cnic_data != '')).sum(),
        'Null/Empty': null_cnics,
    }
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Pie chart
    colors_cnic = [COLORS['success'], COLORS['warning'], '#E67E22', COLORS['neutral']]
    wedges, texts, autotexts = ax1.pie(cnic_breakdown.values(), labels=cnic_breakdown.keys(),
                                        autopct='%1.1f%%', colors=colors_cnic, startangle=90)
    ax1.set_title('CNIC Quality Breakdown')
    
    # Summary stats as text
    ax2.axis('off')
    summary_text = (
        f"CNIC INTEGRITY REPORT\n"
        f"{'─' * 35}\n\n"
        f"Total Records:     {total_cnics:,}\n"
        f"Valid & Real:      {valid_real.sum():,}  ({valid_real.sum()/total_cnics*100:.1f}%)\n"
        f"Fake Placeholder:  {fake_cnics:,}  ({fake_cnics/total_cnics*100:.1f}%)\n"
        f"Null/Empty:        {null_cnics:,}  ({null_cnics/total_cnics*100:.1f}%)\n\n"
        f"⚠ Deduplication is IMPOSSIBLE\n"
        f"  with {fake_cnics/total_cnics*100:.0f}% fake CNICs\n\n"
        f"🔴 SEVERITY: CRITICAL"
    )
    ax2.text(0.1, 0.5, summary_text, transform=ax2.transAxes,
            fontsize=12, verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#FFF3CD', edgecolor='#FFC107'))
    
    fig.suptitle('CNIC Data Quality Analysis', fontsize=14, fontweight='bold')
    plt.tight_layout()
    save_chart(fig, "cnic_integrity")
    
    add_finding("PII/CNIC", 
                f"{fake_cnics} records ({fake_cnics/total_cnics*100:.1f}%) use fake placeholder CNIC",
                "CRITICAL")


# ═══════════════════════════════════════════════════════════════════
# BATCH 3: HEARING RECORDS ANALYSIS
# ═══════════════════════════════════════════════════════════════════

print("\n" + "─" * 65)
print("BATCH 3: Hearing Records Analysis")
print("─" * 65)

if not hearings.empty:
    # ── 3.1 Hearings per case distribution ────────────────────────
    print("\n[3.1] Hearings per Case")
    hearing_id_col = None
    for col in ['programsID', 'programs_id', 'program_id', 'case_id']:
        if col in hearings.columns:
            hearing_id_col = col
            break
    
    if hearing_id_col:
        hearings_per_case = hearings[hearing_id_col].value_counts()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Histogram
        ax1.hist(hearings_per_case.values, bins=30, color=COLORS['primary'], 
                 edgecolor='white', alpha=0.85)
        ax1.set_xlabel('Number of Hearings')
        ax1.set_ylabel('Number of Cases')
        ax1.set_title('Distribution of Hearings per Case')
        ax1.axvline(hearings_per_case.mean(), color=COLORS['warning'], 
                    linestyle='--', label=f'Mean: {hearings_per_case.mean():.1f}')
        ax1.axvline(hearings_per_case.median(), color=COLORS['accent'],
                    linestyle='--', label=f'Median: {hearings_per_case.median():.0f}')
        ax1.legend()
        
        # Box plot
        ax2.boxplot(hearings_per_case.values, vert=True, widths=0.5,
                   patch_artist=True, boxprops=dict(facecolor=COLORS['secondary'], alpha=0.6))
        ax2.set_ylabel('Hearings per Case')
        ax2.set_title('Hearing Count Distribution (Box Plot)')
        
        stats_text = (f"Total Hearings: {len(hearings):,}\n"
                     f"Cases with Hearings: {len(hearings_per_case):,}\n"
                     f"Mean: {hearings_per_case.mean():.1f}\n"
                     f"Median: {hearings_per_case.median():.0f}\n"
                     f"Max: {hearings_per_case.max()}")
        ax2.text(0.95, 0.95, stats_text, transform=ax2.transAxes,
                fontsize=10, va='top', ha='right', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightyellow'))
        
        plt.tight_layout()
        save_chart(fig, "hearings_per_case")
        
        # Cases with zero hearings
        cases_with_hearings = set(hearings[hearing_id_col].unique())
        total_cases = len(programs)
        cases_without = total_cases - len(cases_with_hearings)
        pct_without = (cases_without / total_cases) * 100
        add_finding("Hearings", 
                    f"{pct_without:.0f}% of cases ({cases_without:,}) have ZERO hearing records",
                    "CRITICAL" if pct_without > 30 else "MODERATE")
    
    # ── 3.2 Hearing Notes Quality ─────────────────────────────────
    print("\n[3.2] Hearing Notes Quality")
    notes_col = None
    for col in ['hearingProceeding', 'hearing_notes', 'notes', 'proceedings']:
        if col in hearings.columns:
            notes_col = col
            break
    
    if notes_col:
        notes = hearings[notes_col].fillna('')
        notes_lengths = notes.str.len()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(notes_lengths[notes_lengths > 0], bins=50, color=COLORS['accent'],
                edgecolor='white', alpha=0.85)
        ax.set_xlabel('Character Length')
        ax.set_ylabel('Number of Hearing Notes')
        ax.set_title('Hearing Notes — Text Length Distribution')
        ax.axvline(notes_lengths[notes_lengths > 0].median(), color=COLORS['warning'],
                  linestyle='--', label=f'Median: {notes_lengths[notes_lengths > 0].median():.0f} chars')
        ax.legend()
        plt.tight_layout()
        save_chart(fig, "hearing_notes_length")
        
        empty_notes = (notes_lengths == 0).sum()
        short_notes = ((notes_lengths > 0) & (notes_lengths < 20)).sum()
        nlp_ready = (notes_lengths >= 50).sum()
        add_finding("Hearings", 
                    f"Hearing notes NLP-ready: {nlp_ready/len(hearings)*100:.0f}% (≥50 chars)",
                    "INFO")
else:
    print("  ⚠ Hearings data not available — skipping Batch 3")


# ═══════════════════════════════════════════════════════════════════
# BATCH 4: LAWYER PERFORMANCE & COURT ANALYSIS
# ═══════════════════════════════════════════════════════════════════

print("\n" + "─" * 65)
print("BATCH 4: Lawyer Performance & Court Analysis")
print("─" * 65)

# ── 4.1 Lawyer Case Load ─────────────────────────────────────────
print("\n[4.1] Lawyer Case Load")
if 'lawyerName' in programs.columns:
    lawyer_cases = programs['lawyerName'].fillna('UNASSIGNED').value_counts()
    
    fig, ax = plt.subplots(figsize=(12, 7))
    top_lawyers = lawyer_cases.head(15)
    bars = ax.barh(top_lawyers.index[::-1], top_lawyers.values[::-1], 
                   color=COLORS['primary'], alpha=0.85)
    ax.set_xlabel('Number of Cases')
    ax.set_title('Top 15 Lawyers by Case Load')
    for bar, val in zip(bars, top_lawyers.values[::-1]):
        ax.text(bar.get_width() + 3, bar.get_y() + bar.get_height()/2,
                str(val), va='center', fontweight='bold')
    plt.tight_layout()
    save_chart(fig, "lawyer_caseload")

# ── 4.2 Lawyer Win Rates ─────────────────────────────────────────
print("\n[4.2] Lawyer Win Rate Analysis")
if 'lawyerName' in programs.columns and 'caseDecision' in programs.columns:
    decided = programs[programs['caseDecision'].notna() & (programs['caseDecision'] != '')]
    
    if not decided.empty:
        # Determine what counts as a "win"
        win_keywords = ['favour', 'favor', 'won', 'success', 'granted']
        decided['_is_win'] = decided['caseDecision'].str.lower().apply(
            lambda x: any(kw in str(x) for kw in win_keywords))
        
        lawyer_stats = decided.groupby('lawyerName').agg(
            total_decided=('_is_win', 'count'),
            wins=('_is_win', 'sum')
        ).reset_index()
        lawyer_stats['win_rate'] = (lawyer_stats['wins'] / lawyer_stats['total_decided'] * 100).round(1)
        
        # Flag implausible win rates (100% with many cases)
        min_cases = 5
        active = lawyer_stats[lawyer_stats['total_decided'] >= min_cases].sort_values('win_rate', ascending=False)
        suspicious = active[active['win_rate'] == 100.0]
        
        fig, ax = plt.subplots(figsize=(12, 7))
        top_active = active.head(15).sort_values('win_rate')
        colors_wr = [COLORS['warning'] if r['win_rate'] == 100.0 else COLORS['primary'] 
                     for _, r in top_active.iterrows()]
        bars = ax.barh(top_active['lawyerName'], top_active['win_rate'], color=colors_wr)
        ax.set_xlabel('Win Rate (%)')
        ax.set_title(f'Lawyer Win Rates (min {min_cases} decided cases)\nRed = 100% win rate (suspicious)')
        ax.set_xlim(0, 110)
        for bar, (_, row) in zip(bars, top_active.iterrows()):
            ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                    f'{row["win_rate"]}% ({row["wins"]}/{row["total_decided"]})',
                    va='center', fontsize=9)
        plt.tight_layout()
        save_chart(fig, "lawyer_win_rates")
        
        if len(suspicious) > 0:
            add_finding("Lawyers",
                       f"{len(suspicious)} lawyers have 100% win rate — statistically implausible, needs verification",
                       "MODERATE")

# ── 4.3 Court Level Standardization ──────────────────────────────
print("\n[4.3] Court Level Standardization Check")
if 'courtLevel' in programs.columns:
    court_values = programs['courtLevel'].fillna('NOT RECORDED').value_counts()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(court_values.index[::-1], court_values.values[::-1], 
                   color=COLORS['secondary'])
    ax.set_xlabel('Count')
    ax.set_title('Court Level Values (Check for Duplicates/Misspellings)')
    for bar, val in zip(bars, court_values.values[::-1]):
        ax.text(bar.get_width() + 3, bar.get_y() + bar.get_height()/2,
                str(val), va='center')
    plt.tight_layout()
    save_chart(fig, "court_levels")
    
    unique_courts = len(court_values)
    if unique_courts > 7:
        add_finding("Standardization",
                   f"Court level has {unique_courts} unique values — likely contains misspellings (expected ~5)",
                   "CRITICAL")


# ═══════════════════════════════════════════════════════════════════
# BATCH 5: CASE DURATION & TEXT QUALITY
# ═══════════════════════════════════════════════════════════════════

print("\n" + "─" * 65)
print("BATCH 5: Case Duration & Text Quality")
print("─" * 65)

# ── 5.1 Case Facts Text Length Analysis ───────────────────────────
print("\n[5.1] Case Facts — Text Quality for NLP")
if 'caseFacts' in programs.columns:
    facts = programs['caseFacts'].fillna('')
    fact_lengths = facts.str.len()
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Length distribution
    ax1.hist(fact_lengths[fact_lengths > 0], bins=50, color=COLORS['primary'],
             edgecolor='white', alpha=0.85)
    ax1.set_xlabel('Character Length')
    ax1.set_ylabel('Number of Cases')
    ax1.set_title('Case Facts — Text Length Distribution')
    ax1.axvline(100, color=COLORS['warning'], linestyle='--', label='Min for NLP (100 chars)')
    ax1.legend()
    
    # Quality buckets
    buckets = {
        'Empty\n(0 chars)': (fact_lengths == 0).sum(),
        'Too Short\n(1-50 chars)': ((fact_lengths > 0) & (fact_lengths <= 50)).sum(),
        'Marginal\n(51-100 chars)': ((fact_lengths > 50) & (fact_lengths <= 100)).sum(),
        'NLP Ready\n(101-500 chars)': ((fact_lengths > 100) & (fact_lengths <= 500)).sum(),
        'Rich Text\n(500+ chars)': (fact_lengths > 500).sum(),
    }
    
    colors_bucket = [COLORS['warning'], '#E67E22', '#F39C12', COLORS['success'], COLORS['accent']]
    ax2.bar(buckets.keys(), buckets.values(), color=colors_bucket)
    ax2.set_ylabel('Number of Cases')
    ax2.set_title('Case Facts — Quality Buckets')
    for i, (k, v) in enumerate(buckets.items()):
        ax2.text(i, v + 5, f'{v}\n({v/len(programs)*100:.0f}%)', ha='center', fontsize=9)
    
    plt.tight_layout()
    save_chart(fig, "casefacts_quality")
    
    nlp_ready_pct = (fact_lengths > 100).sum() / len(programs) * 100
    add_finding("Text Quality",
               f"Case facts NLP-ready (>100 chars): {nlp_ready_pct:.1f}%",
               "CRITICAL" if nlp_ready_pct < 50 else "MODERATE" if nlp_ready_pct < 80 else "INFO")

# ── 5.2 Case Duration Analysis ────────────────────────────────────
print("\n[5.2] Case Duration Analysis")
filing_col = None
disposal_col = None
for col in ['caseFilingDate', 'case_filing_date']:
    if col in programs.columns:
        filing_col = col
        break
for col in ['caseDecisionDate', 'disposalDate', 'case_decision_date']:
    if col in programs.columns:
        disposal_col = col
        break

if filing_col and disposal_col:
    programs['_filing'] = pd.to_datetime(programs[filing_col], errors='coerce')
    programs['_disposal'] = pd.to_datetime(programs[disposal_col], errors='coerce')
    programs['_duration_days'] = (programs['_disposal'] - programs['_filing']).dt.days
    
    valid_duration = programs['_duration_days'].dropna()
    valid_duration = valid_duration[(valid_duration >= 0) & (valid_duration < 3650)]  # 0-10 years
    
    if len(valid_duration) > 10:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        ax1.hist(valid_duration, bins=40, color=COLORS['accent'], edgecolor='white', alpha=0.85)
        ax1.set_xlabel('Days to Disposal')
        ax1.set_ylabel('Number of Cases')
        ax1.set_title('Case Duration Distribution')
        ax1.axvline(valid_duration.mean(), color=COLORS['warning'], linestyle='--',
                   label=f'Mean: {valid_duration.mean():.0f} days')
        ax1.axvline(valid_duration.median(), color=COLORS['primary'], linestyle='--',
                   label=f'Median: {valid_duration.median():.0f} days')
        ax1.legend()
        
        # Duration by case type
        if 'natureOfCase' in programs.columns:
            dur_by_type = programs.dropna(subset=['_duration_days', 'natureOfCase'])
            dur_by_type = dur_by_type[(dur_by_type['_duration_days'] >= 0) & 
                                      (dur_by_type['_duration_days'] < 3650)]
            top_types = dur_by_type['natureOfCase'].value_counts().head(8).index
            dur_by_type = dur_by_type[dur_by_type['natureOfCase'].isin(top_types)]
            
            if not dur_by_type.empty:
                medians = dur_by_type.groupby('natureOfCase')['_duration_days'].median().sort_values()
                ax2.barh(medians.index, medians.values, color=COLORS['secondary'])
                ax2.set_xlabel('Median Days to Disposal')
                ax2.set_title('Case Duration by Type (Median)')
                for bar, val in zip(ax2.patches, medians.values):
                    ax2.text(bar.get_width() + 3, bar.get_y() + bar.get_height()/2,
                            f'{val:.0f}d', va='center')
        
        plt.tight_layout()
        save_chart(fig, "case_duration")
        
        impossible = ((programs['_duration_days'] < 0) | (programs['_duration_days'] > 3650)).sum()
        if impossible > 0:
            add_finding("Dates", 
                       f"{impossible} cases have impossible dates (negative or >10 years)",
                       "CRITICAL")
        
        add_finding("Duration",
                   f"Average case duration: {valid_duration.mean():.0f} days (median: {valid_duration.median():.0f})",
                   "INFO")
else:
    print("  ⚠ Filing/disposal date columns not found for duration analysis")

# ── 5.3 Program (Donor) Breakdown ─────────────────────────────────
print("\n[5.3] Program/Donor Breakdown")
if 'programName' in programs.columns:
    program_counts = programs['programName'].fillna('Unsponsored/Walk-in').value_counts()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(program_counts.index[::-1], program_counts.values[::-1],
                   color=COLORS['primary'], alpha=0.85)
    ax.set_xlabel('Number of Cases')
    ax.set_title('Cases by Program/Donor')
    for bar, val in zip(bars, program_counts.values[::-1]):
        ax.text(bar.get_width() + 3, bar.get_y() + bar.get_height()/2,
                f'{val} ({val/len(programs)*100:.1f}%)', va='center', fontsize=9)
    plt.tight_layout()
    save_chart(fig, "program_breakdown")


# ═══════════════════════════════════════════════════════════════════
# BATCH 6 (NEW): PII DISCOVERY
# ═══════════════════════════════════════════════════════════════════

print("\n" + "─" * 65)
print("BATCH 6: PII Discovery — Identifying Sensitive Fields")
print("─" * 65)

pii_fields = []
pii_keywords = {
    'name': ['name', 'clientName', 'fatherHusbandName', 'lawyerName', 'judgeName'],
    'cnic': ['cnic', 'CNIC', 'nic'],
    'phone': ['mobile', 'phone', 'contact', 'mobileNo'],
    'address': ['address', 'Address', 'location'],
    'email': ['email', 'Email'],
}

print("\n[6.1] Scanning ALL columns across ALL tables for PII...")
tables_to_scan = {
    'programs': programs,
    'hearings': hearings,
    'programs_detail': programs_detail,
    'users': users,
}

pii_inventory = []
for table_name, df in tables_to_scan.items():
    if df.empty:
        continue
    for col in df.columns:
        col_lower = col.lower()
        pii_type = None
        
        # Check by column name
        if any(kw.lower() in col_lower for kw in ['name', 'client', 'father', 'husband']):
            pii_type = 'PERSON NAME'
        elif any(kw.lower() in col_lower for kw in ['cnic', 'nic']):
            pii_type = 'NATIONAL ID (CNIC)'
        elif any(kw.lower() in col_lower for kw in ['mobile', 'phone', 'contact']):
            pii_type = 'PHONE NUMBER'
        elif any(kw.lower() in col_lower for kw in ['address', 'addr']):
            pii_type = 'ADDRESS'
        elif any(kw.lower() in col_lower for kw in ['email']):
            pii_type = 'EMAIL'
        elif any(kw.lower() in col_lower for kw in ['age', 'dob', 'birth']):
            pii_type = 'AGE/DOB'
        
        if pii_type:
            sample = df[col].dropna().head(3).tolist() if col in df.columns else []
            non_null = df[col].notna().sum() if col in df.columns else 0
            pii_inventory.append({
                'table': table_name,
                'column': col,
                'pii_type': pii_type,
                'non_null_count': non_null,
                'sample_values': str(sample)[:100]  # Truncate samples
            })

pii_df = pd.DataFrame(pii_inventory)
if not pii_df.empty:
    print(f"\n  Found {len(pii_df)} PII columns across all tables:")
    for _, row in pii_df.iterrows():
        print(f"    [{row['pii_type']:20s}] {row['table']}.{row['column']} ({row['non_null_count']:,} values)")
    
    # Save PII inventory
    pii_df.to_csv(OUTPUT_DIR / "pii_inventory.csv", index=False)
    print(f"\n  ✓ PII inventory saved to {OUTPUT_DIR / 'pii_inventory.csv'}")
    
    # PII summary chart
    fig, ax = plt.subplots(figsize=(10, 5))
    pii_summary = pii_df.groupby('pii_type')['non_null_count'].sum().sort_values(ascending=True)
    bars = ax.barh(pii_summary.index, pii_summary.values, color=COLORS['warning'])
    ax.set_xlabel('Total PII Values Found')
    ax.set_title('PII Discovery — Sensitive Data Inventory')
    for bar, val in zip(bars, pii_summary.values):
        ax.text(bar.get_width() + 10, bar.get_y() + bar.get_height()/2,
                f'{val:,}', va='center', fontweight='bold')
    plt.tight_layout()
    save_chart(fig, "pii_discovery")
    
    add_finding("PII", f"Found {len(pii_df)} PII columns containing {pii_df['non_null_count'].sum():,} total values",
               "CRITICAL")
else:
    print("  No PII columns detected (unusual — check column names)")


# ═══════════════════════════════════════════════════════════════════
# AI READINESS SCORE
# ═══════════════════════════════════════════════════════════════════

print("\n" + "─" * 65)
print("AI READINESS SCORE CALCULATION")
print("─" * 65)

# Score based on completeness + quality checks
score_components = {}

# 1. Data volume (max 10 pts)
n_cases = len(programs)
score_components['Data Volume'] = min(10, n_cases / 500 * 10)

# 2. Field completeness (max 20 pts)
if completeness_data:
    avg_completeness = np.mean([r['pct'] for r in completeness_data])
    score_components['Field Completeness'] = avg_completeness / 100 * 20

# 3. Hearing coverage (max 15 pts)
if not hearings.empty and hearing_id_col:
    hearing_coverage = len(set(hearings[hearing_id_col].unique())) / len(programs)
    score_components['Hearing Coverage'] = min(15, hearing_coverage * 15)
else:
    score_components['Hearing Coverage'] = 0

# 4. Text quality for NLP (max 20 pts)
if 'caseFacts' in programs.columns:
    nlp_pct = (programs['caseFacts'].fillna('').str.len() > 100).sum() / len(programs)
    score_components['Text Quality (NLP)'] = nlp_pct * 20
else:
    score_components['Text Quality (NLP)'] = 0

# 5. Outcome labels (max 15 pts)
if 'caseDecision' in programs.columns:
    outcome_pct = programs['caseDecision'].notna().sum() / len(programs)
    score_components['Outcome Labels'] = outcome_pct * 15
else:
    score_components['Outcome Labels'] = 0

# 6. Data consistency (max 10 pts) — deduct for issues
consistency_score = 10
critical_count = sum(1 for f in findings if f['severity'] == 'CRITICAL')
consistency_score -= min(10, critical_count * 2)
score_components['Data Consistency'] = max(0, consistency_score)

# 7. PII handling readiness (max 10 pts) — 0 if not handled yet
score_components['PII Handled'] = 0  # Will improve after Phase 3

total_score = sum(score_components.values())

# Chart
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))

# Gauge-like bar
categories = list(score_components.keys())
scores = list(score_components.values())
max_scores = [10, 20, 15, 20, 15, 10, 10]

x = np.arange(len(categories))
ax1.barh(categories, max_scores, color=COLORS['neutral'], alpha=0.3, label='Maximum')
ax1.barh(categories, scores, color=[COLORS['success'] if s/m > 0.7 else 
         COLORS['warning'] if s/m > 0.4 else COLORS['warning'] 
         for s, m in zip(scores, max_scores)], label='Actual')
ax1.set_xlabel('Points')
ax1.set_title('AI Readiness — Component Scores')
for i, (s, m) in enumerate(zip(scores, max_scores)):
    ax1.text(m + 0.3, i, f'{s:.1f}/{m}', va='center', fontsize=10)
ax1.legend(loc='lower right')

# Overall score donut
score_color = COLORS['success'] if total_score >= 80 else COLORS['warning'] if total_score >= 60 else COLORS['warning']
ax2.pie([total_score, 100 - total_score], colors=[score_color, '#EEEEEE'],
        startangle=90, counterclock=False, wedgeprops=dict(width=0.3))
ax2.text(0, 0, f'{total_score:.0f}/100', ha='center', va='center',
        fontsize=36, fontweight='bold', color=score_color)
ax2.set_title('Overall AI Readiness Score', pad=20)

fig.suptitle('LAS CMS — AI Readiness Assessment', fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()
save_chart(fig, "ai_readiness_score")

print(f"\n  🎯 AI Readiness Score: {total_score:.0f} / 100")


# ═══════════════════════════════════════════════════════════════════
# GENERATE SUMMARY REPORT
# ═══════════════════════════════════════════════════════════════════

print("\n" + "─" * 65)
print("GENERATING SUMMARY REPORT")
print("─" * 65)

# Summary text file
report_lines = [
    "=" * 65,
    "  LAS CMS — PHASE 2 DATA ANALYSIS SUMMARY",
    f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    f"  Analysis Tool: Python (pandas + matplotlib)",
    "=" * 65,
    "",
    f"Total Cases Analyzed: {len(programs):,}",
    f"Total Hearings:       {len(hearings):,}",
    f"Total Charts Generated: {chart_count}",
    f"AI Readiness Score:   {total_score:.0f}/100",
    "",
    "─" * 65,
    "KEY FINDINGS",
    "─" * 65,
    "",
]

for sev in ['CRITICAL', 'MODERATE', 'INFO']:
    sev_findings = [f for f in findings if f['severity'] == sev]
    if sev_findings:
        icon = '🔴' if sev == 'CRITICAL' else '🟡' if sev == 'MODERATE' else '🟢'
        report_lines.append(f"\n{icon} {sev} ({len(sev_findings)} findings):")
        for f in sev_findings:
            report_lines.append(f"  • [{f['category']}] {f['finding']}")

report_lines.extend([
    "",
    "─" * 65,
    "AI READINESS SCORE BREAKDOWN",
    "─" * 65,
    "",
])
for comp, score in score_components.items():
    report_lines.append(f"  {comp:25s}: {score:5.1f} pts")
report_lines.append(f"  {'─' * 35}")
report_lines.append(f"  {'TOTAL':25s}: {total_score:5.0f} / 100")

report_lines.extend([
    "",
    "─" * 65,
    "NEXT STEPS (Phase 3)",
    "─" * 65,
    "",
    "  Phase 3.1 — PII Removal",
    "    □ Anonymize CNIC numbers",
    "    □ Mask client/father names",
    "    □ Remove phone numbers",
    "    □ Keep lawyer names (public record)",
    "",
    "  Phase 3.2 — Data Cleaning (8 tasks)",
    "    □ Standardize court level spellings",
    "    □ Parse text dates to datetime",
    "    □ Standardize caseDecision values",
    "    □ Handle 929 fake CNIC records",
    "    □ Fill/flag missing outcomes",
    "    □ Standardize natureOfCase",
    "    □ Remove duplicates",
    "    □ Fix impossible dates",
    "",
    "  Phase 3.3 — RAG Preparation",
    "    □ Merge tables into unified case narratives",
    "    □ Add metadata tags",
    "    □ Export as JSON/JSONL for embedding",
    "",
    "=" * 65,
])

report_text = "\n".join(report_lines)
report_path = OUTPUT_DIR / "phase2_summary_report.txt"
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(report_text)

# Also save findings as JSON for programmatic use
findings_path = OUTPUT_DIR / "findings.json"
with open(findings_path, 'w', encoding='utf-8') as f:
    json.dump({
        'generated': datetime.now().isoformat(),
        'total_cases': len(programs),
        'ai_readiness_score': round(total_score, 1),
        'score_components': {k: round(v, 1) for k, v in score_components.items()},
        'findings': findings,
        'chart_count': chart_count,
    }, f, indent=2, ensure_ascii=False)

print(f"\n  ✓ Summary report: {report_path}")
print(f"  ✓ Findings JSON:  {findings_path}")

# ── FINAL SUMMARY ─────────────────────────────────────────────────
print("\n" + "=" * 65)
print("  PHASE 2 ANALYSIS COMPLETE")
print("=" * 65)
print(f"""
  📊 Charts generated:  {chart_count}
  📋 Findings logged:   {len(findings)}
     🔴 Critical:       {sum(1 for f in findings if f['severity'] == 'CRITICAL')}
     🟡 Moderate:       {sum(1 for f in findings if f['severity'] == 'MODERATE')}
     🟢 Info:           {sum(1 for f in findings if f['severity'] == 'INFO')}
  🎯 AI Readiness:     {total_score:.0f}/100
  
  All outputs saved to: {OUTPUT_DIR.resolve()}
  
  NEXT: Run 02_pii_removal.py → 03_data_cleaning.py → 04_rag_prep.py
""")
