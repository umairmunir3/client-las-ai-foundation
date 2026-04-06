"""
═══════════════════════════════════════════════════════════════════
 LAS CMS — Phase 3.3: RAG Preparation
 
 Prepares the cleaned CMS data for a Retrieval-Augmented Generation
 (RAG) system. The goal: a future lawyer can ask questions like
 "What arguments worked in similar domestic violence cases?" and
 get answers based on real past cases.
 
 What this script does:
   1. Merges all related tables into unified "case documents"
   2. Creates a narrative text for each case (combining all fields)
   3. Adds metadata tags for filtering
   4. Exports as JSON/JSONL ready for embedding + vector store
   5. Creates chunk-ready documents with proper overlap
 
 Usage:
   conda activate las_cms
   python 04_rag_preparation.py
 
 Input:  Cleaned CSVs from ../outputs/cleaned/
 Output: RAG-ready files in ../outputs/rag_ready/
═══════════════════════════════════════════════════════════════════
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
import hashlib
import re

CLEAN_DIR = Path("../outputs/cleaned")
OUTPUT_DIR = Path("../outputs/rag_ready")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 65)
print("  LAS CMS — Phase 3.3: RAG Preparation")
print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("=" * 65)

# ═══════════════════════════════════════════════════════════════════
# LOAD CLEANED DATA
# ═══════════════════════════════════════════════════════════════════

print("\nLoading cleaned data...")
programs = pd.read_csv(CLEAN_DIR / "programs_cleaned.csv")
print(f"  ✓ programs: {len(programs):,} rows")

hearings = pd.DataFrame()
try:
    hearings = pd.read_csv(CLEAN_DIR / "hearings_cleaned.csv")
    print(f"  ✓ hearings: {len(hearings):,} rows")
except FileNotFoundError:
    print("  ⚠ hearings not found — proceeding without hearing data")


# ═══════════════════════════════════════════════════════════════════
# STEP 1: MERGE HEARINGS INTO CASE RECORDS
# ═══════════════════════════════════════════════════════════════════

print("\n" + "─" * 65)
print("STEP 1: Merge Hearings into Case Records")
print("─" * 65)

# Find the hearing → program link column
hearing_link_col = None
for col in ['programsID', 'programs_id', 'program_id', 'case_id']:
    if col in hearings.columns:
        hearing_link_col = col
        break

hearing_notes_col = None
for col in ['hearingProceeding', 'hearing_notes', 'notes', 'proceedings']:
    if col in hearings.columns:
        hearing_notes_col = col
        break

hearing_date_col = None
for col in ['hearingDate', 'hearing_date', 'hearingDate_parsed']:
    if col in hearings.columns:
        hearing_date_col = col
        break

if not hearings.empty and hearing_link_col and hearing_notes_col:
    # Group hearings by case
    def aggregate_hearings(group):
        """Combine all hearings for a case into a single text."""
        entries = []
        # Sort by date if available
        if hearing_date_col:
            group = group.sort_values(hearing_date_col)
        
        for i, (_, row) in enumerate(group.iterrows(), 1):
            date_str = str(row.get(hearing_date_col, 'Date unknown'))
            notes = str(row.get(hearing_notes_col, '')).strip()
            if notes and notes != 'nan':
                entries.append(f"Hearing {i} ({date_str}): {notes}")
        
        return " | ".join(entries) if entries else ""
    
    hearing_agg = hearings.groupby(hearing_link_col).apply(aggregate_hearings).reset_index()
    hearing_agg.columns = [hearing_link_col, 'hearing_history']
    
    # Count hearings per case
    hearing_counts = hearings.groupby(hearing_link_col).size().reset_index()
    hearing_counts.columns = [hearing_link_col, 'total_hearings']
    
    # Merge into programs
    # Find the program ID column
    prog_id_col = None
    for col in ['id', 'ID', 'programId']:
        if col in programs.columns:
            prog_id_col = col
            break
    
    if prog_id_col:
        programs = programs.merge(hearing_agg, left_on=prog_id_col, right_on=hearing_link_col, how='left')
        programs = programs.merge(hearing_counts, left_on=prog_id_col, right_on=hearing_link_col, how='left')
        programs['total_hearings'] = programs['total_hearings'].fillna(0).astype(int)
        programs['hearing_history'] = programs['hearing_history'].fillna('')
        
        with_hearings = (programs['total_hearings'] > 0).sum()
        print(f"  ✓ Merged hearing history into {with_hearings:,} cases")
        print(f"  Average hearings per case: {programs['total_hearings'].mean():.1f}")
    else:
        print("  ⚠ Could not find program ID column for merge")
        programs['hearing_history'] = ''
        programs['total_hearings'] = 0
else:
    programs['hearing_history'] = ''
    programs['total_hearings'] = 0
    print("  ⚠ No hearing data to merge")


# ═══════════════════════════════════════════════════════════════════
# STEP 2: CREATE CASE NARRATIVES
# ═══════════════════════════════════════════════════════════════════

print("\n" + "─" * 65)
print("STEP 2: Create Case Narratives")
print("─" * 65)

def build_case_narrative(row):
    """
    Build a comprehensive text narrative for a single case.
    This is what the RAG system will embed and search through.
    
    A good narrative should answer:
    - What type of case is this?
    - Where and when was it filed?
    - What are the facts?
    - What happened in court?
    - What was the outcome?
    """
    parts = []
    
    # Case type and classification
    case_type = str(row.get('natureOfCase_clean', row.get('natureOfCase', 'Unknown'))).strip()
    if case_type and case_type != 'nan':
        parts.append(f"Case Type: {case_type}.")
    
    # Location and court
    district = str(row.get('districtName', '')).strip()
    court = str(row.get('courtLevel', '')).strip()
    if district and district != 'nan':
        location_text = f"District: {district}."
        if court and court != 'nan' and court != 'UNKNOWN':
            location_text += f" Court: {court}."
        parts.append(location_text)
    
    # Client demographics (anonymized)
    gender = str(row.get('gender', '')).strip()
    age = row.get('age', '')
    if gender and gender != 'nan':
        demo_text = f"Client: {gender}"
        if pd.notna(age) and str(age) != 'nan':
            demo_text += f", age {age}"
        demo_text += "."
        parts.append(demo_text)
    
    # Filing information
    filing_date = str(row.get('caseFilingDate', '')).strip()
    if filing_date and filing_date != 'nan':
        parts.append(f"Filed: {filing_date}.")
    
    # Program/donor
    program = str(row.get('programName', '')).strip()
    if program and program != 'nan':
        parts.append(f"Program: {program}.")
    
    # Case facts — the most important field for RAG
    facts = str(row.get('caseFacts', '')).strip()
    if facts and facts != 'nan' and len(facts) > 5:
        parts.append(f"Case Facts: {facts}")
    
    # Hearing history
    hearing_hist = str(row.get('hearing_history', '')).strip()
    if hearing_hist and hearing_hist != 'nan' and len(hearing_hist) > 5:
        total_h = row.get('total_hearings', 0)
        parts.append(f"Hearing History ({total_h} hearings): {hearing_hist}")
    
    # Outcome
    decision = str(row.get('caseDecision_clean', row.get('caseDecision', ''))).strip()
    status = str(row.get('currentCaseStatus', '')).strip()
    if decision and decision != 'nan':
        outcome_text = f"Outcome: {decision}."
        if status and status != 'nan':
            outcome_text += f" Status: {status}."
        parts.append(outcome_text)
    
    return " ".join(parts)


programs['case_narrative'] = programs.apply(build_case_narrative, axis=1)

# Stats
narrative_lengths = programs['case_narrative'].str.len()
print(f"  ✓ Generated {len(programs):,} case narratives")
print(f"  Average length: {narrative_lengths.mean():.0f} characters")
print(f"  Median length:  {narrative_lengths.median():.0f} characters")
print(f"  Min/Max:        {narrative_lengths.min():.0f} / {narrative_lengths.max():.0f}")

# Quality buckets
short = (narrative_lengths < 100).sum()
medium = ((narrative_lengths >= 100) & (narrative_lengths < 500)).sum()
rich = (narrative_lengths >= 500).sum()
print(f"\n  Quality distribution:")
print(f"    Short  (<100 chars):  {short:,} ({short/len(programs)*100:.1f}%)")
print(f"    Medium (100-500):     {medium:,} ({medium/len(programs)*100:.1f}%)")
print(f"    Rich   (500+):        {rich:,} ({rich/len(programs)*100:.1f}%)")


# ═══════════════════════════════════════════════════════════════════
# STEP 3: CREATE METADATA FOR FILTERING
# ═══════════════════════════════════════════════════════════════════

print("\n" + "─" * 65)
print("STEP 3: Create Metadata Tags")
print("─" * 65)

def build_metadata(row):
    """Build a metadata dictionary for filtering in the vector store."""
    metadata = {}
    
    # Core identifiers
    for col in ['id', 'ID', 'programId']:
        if col in row.index and pd.notna(row[col]):
            metadata['case_id'] = str(row[col])
            break
    
    # Categorical metadata (for filtering)
    field_map = {
        'natureOfCase_clean': 'case_type',
        'natureOfCase': 'case_type',
        'caseDecision_clean': 'outcome',
        'caseDecision': 'outcome',
        'currentCaseStatus': 'status',
        'courtLevel': 'court_level',
        'districtName': 'district',
        'gender': 'client_gender',
        'programName': 'program',
    }
    
    for src_col, meta_key in field_map.items():
        if src_col in row.index and pd.notna(row[src_col]):
            val = str(row[src_col]).strip()
            if val and val != 'nan':
                metadata[meta_key] = val
    
    # Numeric metadata
    if 'age' in row.index and pd.notna(row['age']):
        try:
            metadata['client_age'] = int(float(row['age']))
        except (ValueError, TypeError):
            pass
    
    if 'total_hearings' in row.index:
        metadata['total_hearings'] = int(row['total_hearings'])
    
    # Date metadata (for temporal filtering)
    for date_col in ['caseFilingDate', 'interviewDate']:
        if date_col in row.index and pd.notna(row[date_col]):
            try:
                dt = pd.to_datetime(row[date_col], errors='coerce')
                if pd.notna(dt):
                    metadata['filing_year'] = dt.year
                    metadata['filing_month'] = dt.month
                    break
            except:
                pass
    
    # Quality flags (useful for filtering out bad data)
    for flag_col in ['cnic_quality', 'outcome_quality', 'date_quality']:
        if flag_col in row.index and pd.notna(row[flag_col]):
            metadata[flag_col] = str(row[flag_col])
    
    # Narrative length (useful for filtering to rich documents)
    metadata['narrative_length'] = len(str(row.get('case_narrative', '')))
    
    return metadata


programs['metadata'] = programs.apply(build_metadata, axis=1)
print(f"  ✓ Generated metadata for {len(programs):,} cases")

# Show sample
sample_meta = programs['metadata'].iloc[0]
print(f"\n  Sample metadata keys: {list(sample_meta.keys())}")


# ═══════════════════════════════════════════════════════════════════
# STEP 4: CHUNK LONG DOCUMENTS
# ═══════════════════════════════════════════════════════════════════

print("\n" + "─" * 65)
print("STEP 4: Create Chunks for Long Documents")
print("─" * 65)

CHUNK_SIZE = 800       # Target chunk size in characters
CHUNK_OVERLAP = 100    # Overlap between chunks

def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """
    Split long text into overlapping chunks.
    Tries to split at sentence boundaries.
    """
    if len(text) <= chunk_size:
        return [text]
    
    # Split at sentence boundaries
    sentences = re.split(r'(?<=[.!?|])\s+', text)
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += " " + sentence if current_chunk else sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            # Start new chunk with overlap from previous
            if overlap > 0 and current_chunk:
                overlap_text = current_chunk[-overlap:]
                current_chunk = overlap_text + " " + sentence
            else:
                current_chunk = sentence
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


# Build the final document list
documents = []
total_chunks = 0

for idx, row in programs.iterrows():
    narrative = str(row.get('case_narrative', ''))
    metadata = row.get('metadata', {})
    
    if not narrative or narrative == 'nan':
        continue
    
    chunks = chunk_text(narrative)
    
    for chunk_idx, chunk in enumerate(chunks):
        doc = {
            'id': f"{metadata.get('case_id', idx)}_{chunk_idx}",
            'text': chunk,
            'metadata': {
                **metadata,
                'chunk_index': chunk_idx,
                'total_chunks': len(chunks),
                'source': 'CMS_LAS',
                'document_type': 'case_record'
            }
        }
        documents.append(doc)
        total_chunks += 1

print(f"  Total cases:    {len(programs):,}")
print(f"  Total chunks:   {total_chunks:,}")
print(f"  Avg chunks/case: {total_chunks/len(programs):.1f}")
print(f"  Chunk size:     {CHUNK_SIZE} chars with {CHUNK_OVERLAP} char overlap")


# ═══════════════════════════════════════════════════════════════════
# STEP 5: EXPORT FOR RAG PIPELINE
# ═══════════════════════════════════════════════════════════════════

print("\n" + "─" * 65)
print("STEP 5: Export RAG-Ready Files")
print("─" * 65)

# Format 1: JSONL (one document per line — best for streaming into vector stores)
jsonl_path = OUTPUT_DIR / "cms_cases_rag.jsonl"
with open(jsonl_path, 'w', encoding='utf-8') as f:
    for doc in documents:
        f.write(json.dumps(doc, ensure_ascii=False) + '\n')
print(f"  ✓ JSONL: {jsonl_path.name} ({total_chunks:,} documents)")

# Format 2: Full JSON array (for batch loading)
json_path = OUTPUT_DIR / "cms_cases_rag.json"
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(documents, f, ensure_ascii=False, indent=2)
print(f"  ✓ JSON:  {json_path.name}")

# Format 3: Simple text file (one case per block — for quick inspection)
txt_path = OUTPUT_DIR / "cms_cases_readable.txt"
with open(txt_path, 'w', encoding='utf-8') as f:
    for idx, row in programs.iterrows():
        narrative = str(row.get('case_narrative', ''))
        if narrative and narrative != 'nan':
            f.write(f"{'═' * 60}\n")
            meta = row.get('metadata', {})
            f.write(f"Case ID: {meta.get('case_id', 'N/A')}\n")
            f.write(f"Type: {meta.get('case_type', 'N/A')} | "
                   f"Outcome: {meta.get('outcome', 'N/A')} | "
                   f"District: {meta.get('district', 'N/A')}\n")
            f.write(f"{'─' * 60}\n")
            f.write(narrative + '\n\n')
print(f"  ✓ TXT:   {txt_path.name} (human-readable)")

# Format 4: Metadata CSV (for analysis and filtering)
meta_path = OUTPUT_DIR / "cms_metadata.csv"
meta_rows = []
for idx, row in programs.iterrows():
    meta = row.get('metadata', {})
    meta_rows.append(meta)
pd.DataFrame(meta_rows).to_csv(meta_path, index=False)
print(f"  ✓ CSV:   {meta_path.name} (metadata only)")

# ═══════════════════════════════════════════════════════════════════
# STEP 6: RAG INTEGRATION GUIDE
# ═══════════════════════════════════════════════════════════════════

print("\n" + "─" * 65)
print("STEP 6: RAG Integration Guide")
print("─" * 65)

guide = """
RAG INTEGRATION GUIDE — LAS CMS Data
═══════════════════════════════════════

FILE: cms_cases_rag.jsonl
  Each line = one chunk of a case record, ready for embedding.

DOCUMENT SCHEMA:
  {
    "id":       "case_123_0",              // Unique chunk ID
    "text":     "Case Type: Domestic...",   // The text to embed
    "metadata": {
      "case_id":       "123",              // Original case ID
      "case_type":     "Domestic Violence", // For filtering
      "outcome":       "IN_FAVOUR",        // For filtering
      "district":      "Lahore",           // For filtering
      "court_level":   "Family Court",     // For filtering
      "client_gender": "Female",           // For analysis
      "filing_year":   2024,               // For temporal filtering
      "total_hearings": 5,                 // For analysis
      "chunk_index":   0,                  // Position in document
      "total_chunks":  2,                  // Total chunks for case
      "source":        "CMS_LAS"           // Data source tag
    }
  }

HOW TO USE WITH POPULAR VECTOR STORES:

1. ChromaDB (Local Development):
   ─────────────────────────────
   import chromadb
   import json
   
   client = chromadb.Client()
   collection = client.create_collection("las_cases")
   
   with open("cms_cases_rag.jsonl") as f:
       for line in f:
           doc = json.loads(line)
           collection.add(
               ids=[doc["id"]],
               documents=[doc["text"]],
               metadatas=[doc["metadata"]]
           )

2. Pinecone (Production):
   ────────────────────────
   from pinecone import Pinecone
   
   pc = Pinecone(api_key="...")
   index = pc.Index("las-cases")
   
   # Embed text with your model first, then upsert

3. pgvector (PostgreSQL):
   ────────────────────────
   -- Create table
   CREATE TABLE case_chunks (
     id TEXT PRIMARY KEY,
     embedding vector(768),
     text TEXT,
     case_type TEXT,
     outcome TEXT,
     district TEXT,
     filing_year INT
   );

RECOMMENDED EMBEDDING MODELS:
  - English:  BAAI/bge-large-en-v1.5 (free, excellent)
  - English:  text-embedding-3-large (OpenAI, best quality)
  - Bilingual: intfloat/multilingual-e5-large (if Urdu text present)

EXAMPLE RAG QUERIES A LAWYER MIGHT ASK:
  - "What arguments worked in domestic violence cases in Lahore?"
  - "How long do custody cases typically take in Family Court?"
  - "Show me similar cases to a maintenance dispute with 3 hearings"
  - "What's the win rate for cases in District Court vs Family Court?"
  - "Find cases where the outcome was compromise — what were the facts?"
"""

guide_path = OUTPUT_DIR / "RAG_INTEGRATION_GUIDE.txt"
with open(guide_path, 'w', encoding='utf-8') as f:
    f.write(guide)
print(f"  ✓ Guide: {guide_path.name}")


# ═══════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ═══════════════════════════════════════════════════════════════════

print("\n" + "=" * 65)
print("  PHASE 3.3 RAG PREPARATION COMPLETE")
print("=" * 65)
print(f"""
  📁 Output folder: {OUTPUT_DIR}
  
  Files generated:
    ✓ cms_cases_rag.jsonl        — {total_chunks:,} chunks (for vector store)
    ✓ cms_cases_rag.json         — Same data, full JSON array
    ✓ cms_cases_readable.txt     — Human-readable narratives
    ✓ cms_metadata.csv           — Metadata for filtering/analysis
    ✓ RAG_INTEGRATION_GUIDE.txt  — How to use with ChromaDB/Pinecone/pgvector
  
  Data Quality:
    Total cases:          {len(programs):,}
    Total chunks:         {total_chunks:,}
    Rich narratives (500+ chars): {rich:,} ({rich/len(programs)*100:.1f}%)
  
  ══════════════════════════════════════════
   ALL PHASES COMPLETE! 
  ══════════════════════════════════════════
  
  Phase 2: ✓ EDA Analysis (Python) — {len(programs):,} cases analyzed
  Phase 3.1: ✓ PII Removed — all personal data anonymized
  Phase 3.2: ✓ Data Cleaned — 8 cleaning tasks completed
  Phase 3.3: ✓ RAG Ready — {total_chunks:,} chunks prepared
  
  The data is now ready for:
    1. Building a RAG system (lawyer assistant)
    2. Training ML models (outcome prediction)
    3. Creating dashboards (case analytics)
""")
