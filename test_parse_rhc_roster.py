#!/usr/bin/env python3
"""
Tests for the RHC Roster parsing script.
Ensures data consistency for regular monthly runs.
"""

import csv
from datetime import date
from pathlib import Path

import pytest

from parse_rhc_roster import (
    DATA_DIR,
    PDF_DIR,
    is_entry_header,
    parse_entry_lines,
    parse_pdf,
    save_to_csv,
)


class TestEntryHeaderDetection:
    """Tests for detecting entry header lines."""

    def test_valid_header(self):
        assert is_entry_header("ADAMS (GAGE) - 68301 RHC-C")
        assert is_entry_header("ALLIANCE (BOX BUTTE) - 69301 RHC-C")
        assert is_entry_header("GRAND ISLAND (HALL) - 68801 RHC-C")
        # Town names with apostrophes
        assert is_entry_header("O' NEILL (HOLT) - 68763 RHC-C")

    def test_invalid_header(self):
        assert not is_entry_header("ADAMS PRIMARY CARE 283499")
        assert not is_entry_header("(402) 988-2188 FAX:")
        assert not is_entry_header("TOWN (County) Zip Code")
        assert not is_entry_header("")


class TestParseEntryLines:
    """Tests for parsing individual clinic entries."""

    def test_complete_entry(self):
        lines = [
            "ADAMS (GAGE) - 68301 RHC-C",
            "ADAMS PRIMARY CARE 283499",
            "PO BOX 963, 620 MAIN STREET, SUITE A",
            "(402) 988-2188 FAX:",
            "JOHNSON COUNTY HOSPITAL",
            "MARY KENT, ADMINISTRATOR",
        ]
        entry = parse_entry_lines(lines)

        assert entry["town"] == "ADAMS"
        assert entry["county"] == "GAGE"
        assert entry["zip_code"] == "68301"
        assert entry["facility_type"] == "RHC-C"
        assert entry["facility_name"] == "ADAMS PRIMARY CARE"
        assert entry["provider_id"] == "283499"
        assert entry["address"] == "PO BOX 963, 620 MAIN STREET, SUITE A"
        assert entry["phone"] == "(402) 988-2188"
        assert entry["fax"] == ""
        assert entry["licensee"] == "JOHNSON COUNTY HOSPITAL"
        assert entry["administrator"] == "MARY KENT, ADMINISTRATOR"
        assert entry["care_of"] == ""

    def test_entry_with_fax(self):
        lines = [
            "ARAPAHOE (FURNAS) - 68922 RHC-C",
            "ARAPAHOE MEDICAL CLINIC 283976",
            "P.O. BOX 389, 305 NEBRASKA AVENUE",
            "(308) 962-8495 FAX:(308) 962-7916",
            "TRI VALLEY HEALTH SYSTEM",
            "CLAY JORDAN, ADMINISTRATOR",
        ]
        entry = parse_entry_lines(lines)

        assert entry["phone"] == "(308) 962-8495"
        assert entry["fax"] == "(308) 962-7916"

    def test_entry_with_care_of(self):
        lines = [
            "AINSWORTH (BROWN) - 69210 RHC-C",
            "Brown County Hospital d/b/a Ainsworth Family Clinic 288520",
            "913 EAST ZERO STREET",
            "(402) 387-1900 FAX:",
            "BROWN COUNTY HOSPITAL",
            "MIRYA HALLOCK, ADMINISTRATOR",
            "c/o: SHANNON M SORENSON AINSWORTH FAMILY CLINIC, 945 EAST ZERO STREET, AINSWORTH NE 69210",
        ]
        entry = parse_entry_lines(lines)

        assert entry["care_of"] == "SHANNON M SORENSON AINSWORTH FAMILY CLINIC, 945 EAST ZERO STREET, AINSWORTH NE 69210"

    def test_two_word_town_name(self):
        lines = [
            "GRAND ISLAND (HALL) - 68801 RHC-C",
            "Test Clinic 123456",
            "123 Main St",
            "(308) 555-1234 FAX:",
            "Test Licensee",
            "Test Admin",
        ]
        entry = parse_entry_lines(lines)

        assert entry["town"] == "GRAND ISLAND"
        assert entry["county"] == "HALL"

    def test_town_name_with_apostrophe(self):
        lines = [
            "O' NEILL (HOLT) - 68763 RHC-C",
            "Test Clinic 123456",
            "123 Main St",
            "(402) 555-1234 FAX:",
            "Test Licensee",
            "Test Admin",
        ]
        entry = parse_entry_lines(lines)

        assert entry["town"] == "O' NEILL"
        assert entry["county"] == "HOLT"
        assert entry["zip_code"] == "68763"

    def test_empty_lines(self):
        entry = parse_entry_lines([])
        assert entry["facility_name"] == ""


class TestParsePdf:
    """Tests for PDF parsing functionality."""

    @pytest.fixture
    def sample_pdf(self):
        """Get a sample PDF for testing."""
        # Look for any existing PDF in the pdf directory
        pdf_files = list(PDF_DIR.glob("*.pdf"))
        if pdf_files:
            return pdf_files[0]
        pytest.skip("No PDF file available for testing")

    def test_parse_returns_list(self, sample_pdf):
        entries = parse_pdf(sample_pdf)
        assert isinstance(entries, list)

    def test_parse_returns_expected_count(self, sample_pdf):
        """Verify we parse the expected number of facilities (127 as of Jan 2026)."""
        entries = parse_pdf(sample_pdf)
        # Allow for some variance as facilities may be added/removed
        assert len(entries) >= 100, f"Expected at least 100 entries, got {len(entries)}"
        assert len(entries) <= 200, f"Expected at most 200 entries, got {len(entries)}"

    def test_all_entries_have_required_fields(self, sample_pdf):
        """Every entry must have essential fields populated."""
        entries = parse_pdf(sample_pdf)

        for i, entry in enumerate(entries):
            assert entry["town"], f"Entry {i} missing town"
            assert entry["county"], f"Entry {i} missing county"
            assert entry["zip_code"], f"Entry {i} missing zip_code"
            assert entry["facility_name"], f"Entry {i} missing facility_name"
            assert entry["provider_id"], f"Entry {i} missing provider_id"

    def test_zip_codes_are_valid(self, sample_pdf):
        """All zip codes should be 5-digit Nebraska codes."""
        entries = parse_pdf(sample_pdf)

        for entry in entries:
            zip_code = entry["zip_code"]
            assert len(zip_code) == 5, f"Invalid zip code length: {zip_code}"
            assert zip_code.isdigit(), f"Zip code not numeric: {zip_code}"
            # Nebraska zip codes start with 68 or 69
            assert zip_code.startswith(("68", "69")), f"Non-Nebraska zip code: {zip_code}"

    def test_provider_ids_are_valid(self, sample_pdf):
        """All provider IDs should be 6-digit numbers."""
        entries = parse_pdf(sample_pdf)

        for entry in entries:
            provider_id = entry["provider_id"]
            assert len(provider_id) == 6, f"Invalid provider ID length: {provider_id}"
            assert provider_id.isdigit(), f"Provider ID not numeric: {provider_id}"

    def test_phone_numbers_format(self, sample_pdf):
        """Phone numbers should be in expected format."""
        entries = parse_pdf(sample_pdf)

        for entry in entries:
            phone = entry["phone"]
            if phone:  # Phone is optional
                # Should match format: (XXX) XXX-XXXX
                import re
                assert re.match(r"^\(\d{3}\) \d{3}-\d{4}$", phone), f"Invalid phone format: {phone}"

    def test_facility_types_are_rhc(self, sample_pdf):
        """All facilities should be RHC type."""
        entries = parse_pdf(sample_pdf)

        for entry in entries:
            assert entry["facility_type"].startswith("RHC-"), f"Invalid facility type: {entry['facility_type']}"

    def test_no_duplicate_provider_ids(self, sample_pdf):
        """Each provider ID should be unique."""
        entries = parse_pdf(sample_pdf)
        provider_ids = [e["provider_id"] for e in entries]

        duplicates = [pid for pid in provider_ids if provider_ids.count(pid) > 1]
        assert not duplicates, f"Duplicate provider IDs found: {set(duplicates)}"


class TestSaveToCsv:
    """Tests for CSV output functionality."""

    def test_csv_created_with_correct_name(self, tmp_path, monkeypatch):
        """CSV file should be created with date in filename."""
        monkeypatch.setattr("parse_rhc_roster.DATA_DIR", tmp_path)

        entries = [
            {
                "town": "TEST",
                "county": "COUNTY",
                "zip_code": "68000",
                "facility_type": "RHC-C",
                "facility_name": "Test Clinic",
                "provider_id": "123456",
                "address": "123 Main St",
                "phone": "(402) 555-1234",
                "fax": "",
                "licensee": "Test Hospital",
                "administrator": "Test Admin",
                "care_of": "",
            }
        ]

        test_date = date(2026, 1, 15)
        filepath = save_to_csv(entries, test_date)

        assert filepath.exists()
        assert "2026-01-15" in filepath.name

    def test_csv_has_date_gathered_column(self, tmp_path, monkeypatch):
        """CSV should include date_gathered column."""
        monkeypatch.setattr("parse_rhc_roster.DATA_DIR", tmp_path)

        entries = [
            {
                "town": "TEST",
                "county": "COUNTY",
                "zip_code": "68000",
                "facility_type": "RHC-C",
                "facility_name": "Test Clinic",
                "provider_id": "123456",
                "address": "123 Main St",
                "phone": "(402) 555-1234",
                "fax": "",
                "licensee": "Test Hospital",
                "administrator": "Test Admin",
                "care_of": "",
            }
        ]

        test_date = date(2026, 1, 15)
        filepath = save_to_csv(entries, test_date)

        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row = next(reader)
            assert "date_gathered" in row
            assert row["date_gathered"] == "2026-01-15"

    def test_csv_has_all_expected_columns(self, tmp_path, monkeypatch):
        """CSV should have all expected columns."""
        monkeypatch.setattr("parse_rhc_roster.DATA_DIR", tmp_path)

        entries = [
            {
                "town": "TEST",
                "county": "COUNTY",
                "zip_code": "68000",
                "facility_type": "RHC-C",
                "facility_name": "Test Clinic",
                "provider_id": "123456",
                "address": "123 Main St",
                "phone": "(402) 555-1234",
                "fax": "",
                "licensee": "Test Hospital",
                "administrator": "Test Admin",
                "care_of": "",
            }
        ]

        filepath = save_to_csv(entries, date.today())

        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames

            expected = [
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
            assert fieldnames == expected


class TestDataConsistency:
    """Tests to verify data consistency across runs."""

    @pytest.fixture
    def sample_pdf(self):
        """Get a sample PDF for testing."""
        pdf_files = list(PDF_DIR.glob("*.pdf"))
        if pdf_files:
            return pdf_files[0]
        pytest.skip("No PDF file available for testing")

    def test_parse_is_deterministic(self, sample_pdf):
        """Parsing the same PDF twice should yield identical results."""
        entries1 = parse_pdf(sample_pdf)
        entries2 = parse_pdf(sample_pdf)

        assert entries1 == entries2

    def test_entries_sorted_by_town(self, sample_pdf):
        """Entries should be in alphabetical order by town (as in PDF)."""
        entries = parse_pdf(sample_pdf)
        towns = [e["town"] for e in entries]

        # Note: The PDF is sorted alphabetically by town
        # Verify the order is maintained (allowing for same town with multiple facilities)
        for i in range(len(towns) - 1):
            assert towns[i] <= towns[i + 1], f"Towns not sorted: {towns[i]} > {towns[i+1]}"

    def test_all_facilities_have_addresses(self, sample_pdf):
        """Every facility should have an address."""
        entries = parse_pdf(sample_pdf)

        for entry in entries:
            assert entry["address"], f"Facility {entry['facility_name']} missing address"

    def test_all_facilities_have_licensee(self, sample_pdf):
        """Every facility should have a licensee."""
        entries = parse_pdf(sample_pdf)

        for entry in entries:
            assert entry["licensee"], f"Facility {entry['facility_name']} missing licensee"
