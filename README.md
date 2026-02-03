# Nebraska Rural Health Clinic Roster

This repository tracks Rural Health Clinics (RHCs) in Nebraska by automatically downloading and parsing the official roster published by the Nebraska Department of Health and Human Services (DHHS).

## Data Source

The data is extracted from the [RHC Roster PDF](https://dhhs.ne.gov/licensure/Documents/RHC%20Roster.pdf) published by DHHS Licensure Unit.

## Data Collected

Each clinic record includes:

| Field | Description |
|-------|-------------|
| town | City where the clinic is located |
| county | Nebraska county |
| zip_code | 5-digit ZIP code |
| facility_type | Facility type (e.g., RHC-C) |
| facility_name | Name of the clinic |
| provider_id | 6-digit provider ID |
| address | Street address |
| phone | Phone number |
| fax | Fax number (if available) |
| licensee | Licensee organization |
| administrator | Administrator name and title |
| care_of | Care of address (if available) |
| date_gathered | Date the data was collected |

## Automated Updates

A GitHub Actions workflow runs on the 16th of each month to:
1. Download the latest PDF from DHHS
2. Parse and extract clinic data
3. Run validation tests
4. Commit new data to the repository

## Manual Usage

### Installation

```bash
pip install -r requirements.txt
```

### Run the Script

```bash
python parse_rhc_roster.py
```

This will:
- Download the PDF to `pdf/RHC_Roster_YYYY-MM-DD.pdf`
- Parse all clinic entries
- Save to `data/rhc_roster_YYYY-MM-DD.csv`

### Run Tests

```bash
pytest test_parse_rhc_roster.py -v
```

## Repository Structure

```
├── parse_rhc_roster.py          # Main parsing script
├── test_parse_rhc_roster.py     # Data validation tests
├── requirements.txt             # Python dependencies
├── data/                        # Output CSV files (by date)
├── pdf/                         # Downloaded PDF files (by date)
└── .github/workflows/           # GitHub Actions automation
```

## License

This repository contains public data from the Nebraska DHHS.
