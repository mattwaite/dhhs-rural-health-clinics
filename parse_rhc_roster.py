#!/usr/bin/env python3
"""
Script to download and parse the Nebraska DHHS Rural Health Clinic Roster PDF.
Extracts clinic data and saves to CSV format.
"""

import os
import re
from datetime import date
from pathlib import Path

import pdfplumber
import requests


PDF_URL = "https://dhhs.ne.gov/licensure/Documents/RHC%20Roster.pdf"
PDF_DIR = Path("pdf")
DATA_DIR = Path("data")


def download_pdf(url: str = PDF_URL) -> Path:
    """Download the PDF and save with today's date in filename."""
    PDF_DIR.mkdir(exist_ok=True)
    today = date.today().isoformat()
    filename = f"RHC_Roster_{today}.pdf"
    filepath = PDF_DIR / filename

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    filepath.write_bytes(response.content)
    print(f"Downloaded PDF to: {filepath}")
    return filepath


def parse_entry_lines(lines: list[str]) -> dict:
    """Parse a single clinic entry from its lines."""
    entry = {
        "town": "",
        "county": "",
        "zip_code": "",
        "facility_type": "",
        "facility_name": "",
        "provider_id": "",
        "address": "",
        "phone": "",
        "fax": "",
        "licensee": "",
        "administrator": "",
        "care_of": "",
    }

    if not lines:
        return entry

    # Line 1: TOWN (COUNTY) - ZIP_CODE FACILITY_TYPE
    # Note: Town names may contain apostrophes (e.g., O'NEILL)
    header_match = re.match(
        r"^([A-Z\s']+)\s+\(([A-Z\s]+)\)\s+-\s+(\d{5})\s+(RHC-[A-Z])$",
        lines[0].strip()
    )
    if header_match:
        entry["town"] = header_match.group(1).strip()
        entry["county"] = header_match.group(2).strip()
        entry["zip_code"] = header_match.group(3)
        entry["facility_type"] = header_match.group(4)

    # Line 2: Facility Name and Provider ID
    if len(lines) > 1:
        name_match = re.match(r"^(.+?)\s+(\d{6})$", lines[1].strip())
        if name_match:
            entry["facility_name"] = name_match.group(1).strip()
            entry["provider_id"] = name_match.group(2)
        else:
            entry["facility_name"] = lines[1].strip()

    # Line 3: Address
    if len(lines) > 2:
        entry["address"] = lines[2].strip()

    # Line 4: Phone and Fax
    if len(lines) > 3:
        phone_line = lines[3].strip()
        phone_match = re.match(r"^\((\d{3})\)\s*(\d{3}-\d{4})", phone_line)
        if phone_match:
            entry["phone"] = f"({phone_match.group(1)}) {phone_match.group(2)}"

        fax_match = re.search(r"FAX:\s*\(?(\d{3})\)?\s*(\d{3}-\d{4})", phone_line)
        if fax_match:
            entry["fax"] = f"({fax_match.group(1)}) {fax_match.group(2)}"

    # Line 5: Licensee
    if len(lines) > 4:
        entry["licensee"] = lines[4].strip()

    # Line 6: Administrator
    if len(lines) > 5:
        entry["administrator"] = lines[5].strip()

    # Optional Line 7: c/o (care of)
    for line in lines[6:]:
        if line.strip().startswith("c/o:"):
            entry["care_of"] = line.strip()[4:].strip()
            break

    return entry


def is_entry_header(line: str) -> bool:
    """Check if line is the start of a new clinic entry."""
    # Note: Town names may contain apostrophes (e.g., O'NEILL)
    return bool(re.match(r"^[A-Z\s']+\s+\([A-Z\s]+\)\s+-\s+\d{5}\s+RHC-[A-Z]$", line.strip()))


def parse_pdf(pdf_path: Path) -> list[dict]:
    """Parse the PDF and extract all clinic entries."""
    entries = []

    with pdfplumber.open(pdf_path) as pdf:
        # Skip first page (title page)
        for page in pdf.pages[1:]:
            text = page.extract_text()
            if not text:
                continue

            lines = text.split("\n")

            # Skip header lines (first 7 lines of each page)
            # Line 0: Page header with title and date
            # Lines 1-6: Column labels
            data_lines = lines[7:]

            # Group lines into entries
            current_entry_lines = []

            for line in data_lines:
                # Skip total line
                if line.strip().startswith("Total Facilities:"):
                    continue

                if is_entry_header(line):
                    # Process previous entry if exists
                    if current_entry_lines:
                        entry = parse_entry_lines(current_entry_lines)
                        if entry["facility_name"]:  # Only add valid entries
                            entries.append(entry)
                    current_entry_lines = [line]
                elif current_entry_lines:  # Only append if we've started an entry
                    current_entry_lines.append(line)

            # Process last entry on page
            if current_entry_lines:
                entry = parse_entry_lines(current_entry_lines)
                if entry["facility_name"]:
                    entries.append(entry)

    return entries


def save_to_csv(entries: list[dict], date_gathered: date) -> Path:
    """Save entries to CSV with date gathered column."""
    import csv

    DATA_DIR.mkdir(exist_ok=True)
    today = date_gathered.isoformat()
    filename = f"rhc_roster_{today}.csv"
    filepath = DATA_DIR / filename

    fieldnames = [
        "town",
        "county",
        "zip_code",
        "facility_type",
        "facility_name",
        "provider_id",
        "address",
        "phone",
        "fax",
        "licensee",
        "administrator",
        "care_of",
        "date_gathered",
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for entry in entries:
            row = entry.copy()
            row["date_gathered"] = today
            writer.writerow(row)

    print(f"Saved {len(entries)} entries to: {filepath}")
    return filepath


def main():
    """Main entry point."""
    # Download PDF
    pdf_path = download_pdf()

    # Parse PDF
    entries = parse_pdf(pdf_path)
    print(f"Parsed {len(entries)} clinic entries")

    # Save to CSV
    today = date.today()
    csv_path = save_to_csv(entries, today)

    return csv_path


if __name__ == "__main__":
    main()
