# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository tracks Nebraska Rural Health Clinics by downloading and parsing the official DHHS roster PDF. A GitHub Actions workflow runs monthly on the 16th to collect updated data.

## Commands

```bash
# Run the parsing script (downloads PDF, parses, saves CSV)
python parse_rhc_roster.py

# Run all tests
pytest test_parse_rhc_roster.py -v

# Run a single test
pytest test_parse_rhc_roster.py::TestParsePdf::test_parse_returns_expected_count -v

# Install dependencies
pip install -r requirements.txt

# Manually trigger the GitHub Actions workflow
gh workflow run monthly_update.yml
```

## Architecture

**Data Flow:** PDF download → pdfplumber extraction → regex parsing → CSV output

**Key Files:**
- `parse_rhc_roster.py` - Main script with `download_pdf()`, `parse_pdf()`, `save_to_csv()`
- `test_parse_rhc_roster.py` - Tests for data validation and consistency
- `.github/workflows/monthly_update.yml` - Monthly automation (16th at 9:00 AM UTC)

**Data Directories:**
- `pdf/` - Downloaded PDFs with date suffix (e.g., `RHC_Roster_2026-02-03.pdf`)
- `data/` - Output CSVs with date suffix (e.g., `rhc_roster_2026-02-03.csv`)

## PDF Structure

The source PDF has a title page (skipped) followed by data pages. Each clinic entry spans multiple lines:
1. `TOWN (COUNTY) - ZIP_CODE RHC-C` - Town names may contain apostrophes (O'NEILL)
2. `Facility Name PROVIDER_ID` - 6-digit provider ID at end
3. Address
4. Phone FAX: (optional fax)
5. Licensee
6. Administrator
7. Optional `c/o:` line

Each data page has 7 header lines that must be skipped before parsing entries.
