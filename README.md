# vrcx-query-tools

Tools and scripts for querying and analyzing VRCX database data, including Python/Node scripts and comprehensive schema documentation.

## Overview

This repository contains tools for analyzing your VRChat activity data stored in VRCX's SQLite database. It provides:

- Python scripts for querying location history, join/leave events, and instance statistics
- Hour-by-hour reports of people in instances
- CSV and Excel export capabilities
- Comprehensive database schema documentation

## Prerequisites

- Python 3.7 or higher
- VRCX installed and running (or access to VRCX.sqlite3 database file)
- Windows, Linux, or macOS

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/M1XZG/vrcx-query-tools.git
cd vrcx-query-tools
```

### 2. Create Virtual Environment

On Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

On Linux/macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root (already created if you followed setup):

```ini
# Path to your VRCX data directory
VRCX_DATA_PATH=C:\Users\YourUsername\AppData\Roaming\VRCX

# Database file name (default: VRCX.sqlite3)
VRCX_DB_FILE=VRCX.sqlite3
```

**Important:** The `.env` file contains your local paths and is excluded from git via `.gitignore`.

### 5. Verify VRCX Database Location

The default VRCX database locations are:
- **Windows:** `C:\Users\<Username>\AppData\Roaming\VRCX\VRCX.sqlite3`
- **Linux:** `~/.config/VRCX/VRCX.sqlite3`
- **macOS:** `~/Library/Application Support/VRCX/VRCX.sqlite3`

The script will automatically try to locate your database, but you can specify a custom path using the `VRCX_DATABASE_PATH` environment variable.

## Usage

### Running the Python Query Script

```bash
python vrcx_query.py
```

This will:
1. Connect to your VRCX database
2. Display your location history for today
3. Show an hour-by-hour summary of instances and people
4. Export data to CSV and Excel files in `./vrcx_exports/`

### Querying Specific Dates

Edit the `vrcx_query.py` file and modify the date string in the `main()` function:

```python
# Instead of today's date
today = datetime.now().strftime('%Y-%m-%d')

# Use a specific date
specific_date = '2025-12-25'  # YYYY-MM-DD format
```

### Available Query Functions

The `VRCXQuery` class provides several methods:

- `get_location_history(date_str)` - Your instance visits for a date
- `get_join_leave_events(location, date_str)` - Who joined/left instances
- `get_hour_by_hour_summary(date_str)` - Hourly statistics
- `get_people_in_instances_by_hour(date_str)` - Detailed breakdown
- `get_instance_statistics(date_str)` - Instance visit stats

### Export Formats

The script exports data in two formats:
- **CSV:** `vrcx_exports/vrcx_hourly_YYYY-MM-DD.csv`
- **Excel:** `vrcx_exports/vrcx_hourly_YYYY-MM-DD.xlsx` (with formatting)

## Documentation

Additional documentation in this repository:

- [VRCX_QUERY_GUIDE.md](VRCX_QUERY_GUIDE.md) - Complete query guide
- [DATABASE_SCHEMA_DIAGRAM.md](DATABASE_SCHEMA_DIAGRAM.md) - Database structure
- [DATABASE_STRUCTURE_REVIEW.md](DATABASE_STRUCTURE_REVIEW.md) - Detailed schema analysis

## SQL Queries

Raw SQL queries are available in [vrcx_queries.sql](vrcx_queries.sql) for direct database access.

## Troubleshooting

### Database Not Found

If the script can't find your database:
1. Verify VRCX is installed
2. Check the database path in `.env`
3. Set `VRCX_DATABASE_PATH` environment variable manually

### Permission Errors

Make sure VRCX is closed when running queries, as SQLite may lock the database file.

### Missing Dependencies

If you get import errors:
```bash
pip install -r requirements.txt
```

## Security Notes

- The `.env` file is excluded from git to protect your local paths
- Never commit your actual VRCX database file
- The `.gitignore` file protects sensitive data from being pushed

## Contributing

Feel free to open issues or submit pull requests for improvements.

## License

MIT License - see LICENSE file for details
