#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
#  LAS CMS — Export MySQL Tables to CSV (Run in WSL)
#  
#  This script connects to your local MySQL in WSL and exports
#  all key CMS tables as CSV files to a Windows-accessible folder.
#
#  Usage:
#    chmod +x export_cms_to_csv.sh
#    ./export_cms_to_csv.sh
#
#  Prerequisites:
#    - MySQL running in WSL with the laoorgpk_cmslaravel database
#    - Update MYSQL_PASS below with your actual password
# ═══════════════════════════════════════════════════════════════════

# ── CONFIGURATION ─────────────────────────────────────────────────
MYSQL_USER="root"
MYSQL_PASS="Veteran@123"          # ← UPDATE THIS
DB_NAME="laoorgpk_cmslaravel"

# Output to a Windows-accessible path via WSL
# This creates a folder on your Windows Desktop
WINDOWS_USER=$(cmd.exe /c "echo %USERNAME%" 2>/dev/null | tr -d '\r')
OUTPUT_DIR="/mnt/c/Users/${WINDOWS_USER}/Desktop/LAS_CMS_Data"

# If Windows username detection fails, use this fallback:
# OUTPUT_DIR="/mnt/c/Users/YourWindowsUsername/Desktop/LAS_CMS_Data"

# ── CREATE OUTPUT DIRECTORY ───────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     LAS CMS — MySQL to CSV Export Script                 ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Output directory: $OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

if [ $? -ne 0 ]; then
    echo "ERROR: Could not create output directory."
    echo "Please update OUTPUT_DIR in this script."
    exit 1
fi

# ── TABLES TO EXPORT ─────────────────────────────────────────────
# Core tables (most important for analysis)
CORE_TABLES=(
    "programs"              # Main case records (3,074 rows)
    "hearings"              # Court hearings (14,518 rows)
    "programs_detail"       # Case details (4,687 rows)
    "court"                 # Court records (1,457 rows)
    "case_documents"        # Uploaded documents (774 rows)
    "users"                 # Lawyers/staff (89 rows)
)

# Reference/lookup tables
REF_TABLES=(
    "category"              # Case categories (132 rows)
    "court_name"            # Court names (57 rows)
    "case_stage"            # Case stages (5 rows)
    "police_station"        # Police stations (835 rows)
    "program_transfers"     # Case transfers (178 rows)
    "case_transfer"         # Transfer records (86 rows)
    "notifications"         # Notifications (392 rows)
)

# New interview system tables
INTERVIEW_TABLES=(
    "interviews"                                # Main interviews (131 rows)
    "interview_step1_interviewees"              # Step 1 (124 rows)
    "interview_step2_zakat"                     # Step 2 (124 rows)
    "interview_step3_opposite_party"            # Step 3 (124 rows)
    "interview_step4_eligibility"               # Step 4 (123 rows)
    "interview_step5_case_details"              # Step 5 (123 rows)
    "interview_step6_documents_recommendations" # Step 6 (123 rows)
)

# Monitoring table
OTHER_TABLES=(
    "monitorevaluation"     # M&E records
)

ALL_TABLES=("${CORE_TABLES[@]}" "${REF_TABLES[@]}" "${INTERVIEW_TABLES[@]}" "${OTHER_TABLES[@]}")

# ── TEST CONNECTION ───────────────────────────────────────────────
echo ""
echo "Testing MySQL connection..."
mysql -u "$MYSQL_USER" -p"$MYSQL_PASS" -e "SELECT 1;" "$DB_NAME" > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "ERROR: Cannot connect to MySQL."
    echo "Check MYSQL_USER and MYSQL_PASS in this script."
    echo ""
    echo "Try running manually:"
    echo "  mysql -u root -p -e 'SHOW DATABASES;'"
    exit 1
fi

echo "✓ Connected to MySQL successfully"
echo ""

# ── EXPORT EACH TABLE ─────────────────────────────────────────────
TOTAL=${#ALL_TABLES[@]}
COUNT=0
FAILED=0

echo "Exporting $TOTAL tables to CSV..."
echo "────────────────────────────────────────"

for TABLE in "${ALL_TABLES[@]}"; do
    COUNT=$((COUNT + 1))
    printf "[%2d/%d] %-50s" "$COUNT" "$TOTAL" "$TABLE"
    
    # Check if table exists
    EXISTS=$(mysql -u "$MYSQL_USER" -p"$MYSQL_PASS" -N -e \
        "SELECT COUNT(*) FROM information_schema.tables 
         WHERE table_schema='$DB_NAME' AND table_name='$TABLE';" 2>/dev/null)
    
    if [ "$EXISTS" != "1" ]; then
        echo "⚠ SKIPPED (table not found)"
        FAILED=$((FAILED + 1))
        continue
    fi
    
    # Get row count
    ROW_COUNT=$(mysql -u "$MYSQL_USER" -p"$MYSQL_PASS" -N -e \
        "SELECT COUNT(*) FROM \`$TABLE\`;" "$DB_NAME" 2>/dev/null)
    
    # Export to CSV with headers
    mysql -u "$MYSQL_USER" -p"$MYSQL_PASS" -B -e \
        "SELECT * FROM \`$TABLE\`;" "$DB_NAME" 2>/dev/null \
        | sed 's/\t/,/g' > "$OUTPUT_DIR/${TABLE}.csv"
    
    if [ $? -eq 0 ]; then
        FILE_SIZE=$(du -h "$OUTPUT_DIR/${TABLE}.csv" | cut -f1)
        echo "✓ $ROW_COUNT rows ($FILE_SIZE)"
    else
        echo "✗ FAILED"
        FAILED=$((FAILED + 1))
    fi
done

# ── ALSO EXPORT THE FULL SCHEMA ───────────────────────────────────
echo ""
echo "Exporting database schema..."
mysqldump -u "$MYSQL_USER" -p"$MYSQL_PASS" --no-data "$DB_NAME" \
    > "$OUTPUT_DIR/schema_only.sql" 2>/dev/null
echo "✓ Schema saved to schema_only.sql"

# ── GENERATE A MANIFEST FILE ─────────────────────────────────────
echo ""
echo "Generating manifest..."
cat > "$OUTPUT_DIR/MANIFEST.txt" << MANIFEST_EOF
═══════════════════════════════════════════════════════
 LAS CMS DATA EXPORT MANIFEST
 Exported: $(date '+%Y-%m-%d %H:%M:%S')
 Database: $DB_NAME
 Source: Local MySQL (WSL)
═══════════════════════════════════════════════════════

FILES:
$(ls -lh "$OUTPUT_DIR"/*.csv 2>/dev/null | awk '{print $5, $9}' | sed "s|$OUTPUT_DIR/||")

TOTAL TABLES EXPORTED: $((TOTAL - FAILED)) / $TOTAL
FAILED: $FAILED

NOTE: These CSV files contain REAL client data including
potential PII (names, CNIC numbers, phone numbers).
Handle with care. Do not share publicly.
═══════════════════════════════════════════════════════
MANIFEST_EOF

# ── SUMMARY ───────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                    EXPORT COMPLETE                       ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Tables exported: $((TOTAL - FAILED)) / $TOTAL"
echo "║  Failed:          $FAILED"
echo "║  Output folder:   $OUTPUT_DIR"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "NEXT STEPS:"
echo "  1. Open Windows File Explorer"
echo "  2. Go to Desktop → LAS_CMS_Data folder"
echo "  3. You should see all .csv files there"
echo "  4. Now run the conda setup on Windows (see setup_environment.bat)"
echo ""
