# vrcx-query-tools

Python tools for querying and analyzing VRChat activity data from the VRCX SQLite database.

## Table of Contents

- [About](#about)
- [Command-Line Options](#command-line-options)
- [Quick Start Examples](#quick-start-examples)
- [Available Query Functions](#available-query-functions)
- [Documentation](#documentation)
- [Installation and Setup](#installation-and-setup)
- [Troubleshooting](#troubleshooting)

## About

VRCX logs your VRChat activity to a local SQLite database. This tool lets you query that data to analyze attendance patterns, track visitor statistics, and visualize trends over time.

**Key Features:**

- Query attendance by date, date range, or time period
- Generate hourly, daily, and weekly attendance reports
- Filter by world or specific instance
- Identify peak activity times and busiest days of the week
- Count unique visitors (excluding repeat join/leave events)
- Export data to CSV, Excel, and PNG charts

## Command-Line Options

| Option | Description |
| ------ | ----------- |
| `--date YYYY-MM-DD` | Query a specific date |
| `--start-date YYYY-MM-DD` | Start date for range query |
| `--end-date YYYY-MM-DD` | End date for range query |
| `--average` | Calculate average attendance by hour across date range |
| `--day-of-week` | Show average attendance by day of week (Sunday-Saturday) |
| `--weekly` | Show week-by-week breakdown with day-of-week attendance |
| `--unique` | Count unique visitors only once per day |
| `--list-worlds` | List all worlds visited during a date range |
| `--list-instances` | List all instances for a specific world (requires `--world-id`) |
| `--world-id <id>` | Filter reports to a specific world ID |
| `--world-name <name>` | Optional display name for the world in reports |
| `--instance-id <id>` | Filter reports to a specific instance ID |
| `--export-data` | Export data to CSV and Excel files (charts always generated) |
| `--verbose` | Show verbose output including database information |

## Quick Start Examples

```bash
# Query today's attendance
python vrcx_query.py

# Query a specific date
python vrcx_query.py --date 2025-12-25

# Average attendance across December
python vrcx_query.py --start-date 2025-12-01 --end-date 2025-12-31 --average

# Find busiest days of the week
python vrcx_query.py --start-date 2025-12-01 --end-date 2025-12-31 --day-of-week

# Week-by-week breakdown
python vrcx_query.py --start-date 2025-12-01 --end-date 2025-12-31 --weekly

# Count unique visitors only (not repeated joins)
python vrcx_query.py --start-date 2025-12-01 --end-date 2025-12-31 --day-of-week --unique

# List all worlds visited in a date range
python vrcx_query.py --start-date 2025-12-01 --end-date 2025-12-31 --list-worlds

# Filter by specific world
python vrcx_query.py --date 2025-12-25 --world-id "wrld_..." --world-name "World Name"
```

**See [docs/USAGE_EXAMPLES.md](docs/USAGE_EXAMPLES.md) for comprehensive examples and use cases.**

## Available Query Functions

The `VRCXQuery` class provides methods for programmatic access:

- `get_location_history(date_str)` - Your instance visits for a date
- `get_join_leave_events(location, date_str)` - Who joined/left instances
- `get_hour_by_hour_summary(date_str)` - Hourly statistics for a specific date
- `get_hour_by_hour_average(start_date_str, end_date_str)` - Average attendance across a date range
- `get_people_in_instances_by_hour(date_str)` - Detailed breakdown
- `get_instance_statistics(date_str)` - Instance visit stats
- `get_unique_worlds(start_date_str, end_date_str)` - List all worlds visited in a date range
- `get_unique_instances_for_world(world_id, start_date_str, end_date_str)` - List all instances for a specific world
- `get_hour_by_hour_summary_for_world(world_id, date_str)` - Hourly stats for a specific world
- `get_unique_visitors_by_hour_for_world(world_id, date_str)` - Unique hourly visitors for a specific world
- `get_hour_by_hour_summary_for_instance(instance_id, date_str)` - Hourly stats for a specific instance
- `get_unique_visitors_by_hour_for_instance(instance_id, date_str)` - Unique hourly visitors for a specific instance

## Documentation

Additional documentation:

- [docs/USAGE_EXAMPLES.md](docs/USAGE_EXAMPLES.md) - Comprehensive usage examples and common use cases
- [docs/VRCX_QUERY_GUIDE.md](docs/VRCX_QUERY_GUIDE.md) - Complete query guide
- [docs/DATABASE_SCHEMA_DIAGRAM.md](docs/DATABASE_SCHEMA_DIAGRAM.md) - Database structure
- [docs/DATABASE_STRUCTURE_REVIEW.md](docs/DATABASE_STRUCTURE_REVIEW.md) - Detailed schema analysis
- [docs/vrcx_queries.sql](docs/vrcx_queries.sql) - Raw SQL query examples

## Installation and Setup

### Prerequisites

- Python 3.7 or higher
- VRCX installed (or access to VRCX.sqlite3 database file)
- Windows, Linux, or macOS

### 1. Clone the Repository

```bash
git clone https://github.com/M1XZG/vrcx-query-tools.git
cd vrcx-query-tools
```

### 2. Create Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables (Optional)

The script automatically detects the VRCX database location. To customize paths, create a `.env` file:

```ini
# Path to your VRCX data directory
VRCX_DATA_PATH=C:\Users\YourUsername\AppData\Roaming\VRCX

# Database file name (default: VRCX.sqlite3)
VRCX_DB_FILE=VRCX.sqlite3

# Output directory for reports (default: ./vrcx_exports)
VRCX_REPORTS_OUTPUT_PATH=./vrcx_exports
```

**Default VRCX database locations:**
- **Windows:** `C:\Users\<Username>\AppData\Roaming\VRCX\VRCX.sqlite3`
- **Linux:** `~/.config/VRCX/VRCX.sqlite3`
- **Linux:** `~/.config/VRCX/VRCX.sqlite3`
- **macOS:** `~/Library/Application Support/VRCX/VRCX.sqlite3`

## Troubleshooting

### Database Not Found

If the script can't find your database:

1. Verify VRCX is installed
2. Check the database path in `.env`
3. Set `VRCX_DATABASE_PATH` environment variable manually

### Permission Errors

Close VRCX before running queries, as SQLite may lock the database file.

### Missing Dependencies

If you get import errors:

```bash
pip install -r requirements.txt
```

## Security Notes

- The `.env` file is excluded from git to protect your local paths
- Never commit your VRCX database file
- The `.gitignore` file protects sensitive data

## Contributing

Feel free to open issues or submit pull requests.

## License

MIT License - see LICENSE file for details

