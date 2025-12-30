# VRCX Database Query - Quick Start Guide

## Overview

This guide helps you query the VRCX SQLite database to analyze your VRChat activity, specifically to:

- Track your location/instance timeline throughout the day
- Count how many people were in each instance hour-by-hour
- Export data to spreadsheets for further analysis

---

## Quick Start

### Option 1: Python Script (Recommended)

**Requirements:**

- Python 3.6+
- SQLite3 (usually built-in)
- pandas and openpyxl for Excel export

**Installation:**

```bash
# Install dependencies
pip install pandas openpyxl

# Make script executable (Linux/Mac)
chmod +x vrcx_query.py
```

**Usage:**

```bash
# Run for today's data
python vrcx_query.py

# Run for specific date
python vrcx_query.py 2024-12-30
```

**Output:**

- Console table with hour-by-hour summary
- CSV export: `vrcx_exports/vrcx_hourly_YYYY-MM-DD.csv`
- Excel export: `vrcx_exports/vrcx_hourly_YYYY-MM-DD.xlsx`

---

### Option 2: Node.js Script

**Requirements:**

- Node.js 12+
- better-sqlite3 package

**Installation:**

```bash
# Install dependencies
npm install better-sqlite3

# Make script executable (Linux/Mac)
chmod +x vrcx_query.js
```

**Usage:**

```bash
# Run for today's data
node vrcx_query.js

# Run for specific date
node vrcx_query.js 2024-12-30
```

**Output:**

- Console tables with multiple views
- CSV export: `vrcx_exports/vrcx_hourly_YYYY-MM-DD.csv`
- JSON export: `vrcx_exports/vrcx_hourly_YYYY-MM-DD.json`

---

## Understanding the Data

### Hour-by-Hour Summary

The main output shows:

| Column            | Meaning                                  |
| ----------------- | ---------------------------------------- |
| **Hour**          | Time of day (00:00 to 23:00)             |
| **Instance**      | VRChat instance ID                       |
| **World**         | World name                               |
| **Joins**         | Number of people who joined the instance |
| **Leaves**        | Number of people who left the instance   |
| **Net Change**    | Net change in people (joins - leaves)    |
| **Unique People** | Count of unique people in this hour      |

### Example Output

```
Hour   Instance                           World                          Joins    Leaves   Net    People
────────────────────────────────────────────────────────────────────────────────────────────────────────
12:00  wrld_12345:12345~region(us)       Home                               5        2       3        7
13:00  wrld_12345:12345~region(us)       Home                               2        1       1        8
14:00  wrld_54321:54321~region(eu)       Social Hub                         8        3       5       12
```

---

## Database Location

The script automatically finds your database. If it fails, you can set the environment variable:

**Windows (PowerShell):**

```powershell
$env:VRCX_DATABASE_PATH = "C:\Users\YourUsername\AppData\Roaming\VRCX\VRCX.sqlite3"
python vrcx_query.py
```

**Linux/Mac:**

```bash
export VRCX_DATABASE_PATH="$HOME/.config/VRCX/VRCX.sqlite3"
python vrcx_query.py
```

---

## Advanced Usage

### Custom Queries

The scripts expose a `VRCXQuery` class with these methods:

#### Python

```python
from vrcx_query import VRCXDatabase, VRCXQuery

db = VRCXDatabase("/path/to/VRCX.sqlite3")
db.connect()
query = VRCXQuery(db)

# Get location history
locations = query.get_location_history('2024-12-30')

# Get join/leave events
events = query.get_join_leave_events('2024-12-30')

# Get people in instances by hour
people = query.get_people_in_instances_by_hour('2024-12-30')

# Get instance statistics
stats = query.get_instance_statistics('2024-12-30')

db.close()
```

#### Node.js

```javascript
const Database = require('better-sqlite3');
const db = new Database('/path/to/VRCX.sqlite3', { readonly: true });
const VRCXQuery = require('./vrcx_query.js').VRCXQuery;

const query = new VRCXQuery(db);

// Get location history
const locations = query.getLocationHistory('2024-12-30');

// Get join/leave events
const events = query.getJoinLeaveEvents('2024-12-30');

// Get instance statistics
const stats = query.getInstanceStatistics('2024-12-30');

db.close();
```

### Direct SQL Queries

You can also query the database directly using any SQLite client:

```sql
-- People in instances by hour
SELECT
    CAST(strftime('%H', created_at) AS INTEGER) as hour,
    location,
    world_name,
    SUM(CASE WHEN type = 'join' THEN 1 ELSE 0 END) as joins,
    SUM(CASE WHEN type = 'leave' THEN 1 ELSE 0 END) as leaves,
    COUNT(DISTINCT display_name) as unique_people
FROM gamelog_join_leave
WHERE DATE(created_at) = '2024-12-30'
GROUP BY hour, location
ORDER BY hour ASC;

-- Your location timeline
SELECT
    created_at,
    location,
    world_name,
    time as duration_seconds
FROM gamelog_location
WHERE DATE(created_at) = '2024-12-30'
ORDER BY created_at ASC;

-- Specific location details
SELECT
    created_at,
    type,
    display_name,
    user_id
FROM gamelog_join_leave
WHERE location = 'wrld_12345:12345~region(us)'
  AND DATE(created_at) = '2024-12-30'
ORDER BY created_at ASC;
```

**SQLite CLI Example:**

```bash
sqlite3 "/path/to/VRCX.sqlite3" "SELECT * FROM gamelog_location LIMIT 10;"
```

---

## Troubleshooting

### Database is Locked

**Error:** `database is locked`

**Solution:** Close the VRCX application before running the query script. The database can only be accessed by one application at a time.

```bash
# Linux/Mac - Kill VRCX process
pkill -f VRCX

# Then run query
python vrcx_query.py
```

### Database Not Found

**Error:** `Could not find VRCX.sqlite3 database`

**Solution:** Set the environment variable manually:

```bash
export VRCX_DATABASE_PATH="/path/to/your/VRCX.sqlite3"
python vrcx_query.py
```

### No Data Found

If you get "No data found for this date" but VRCX has been running:

1. Make sure VRCX has actually logged data for that date
2. Try a recent date when VRCX was actively running
3. Check database integrity: `sqlite3 VRCX.sqlite3 "PRAGMA integrity_check;"`

### Missing Dependencies

**Python:**

```bash
pip install --upgrade sqlite3 pandas openpyxl
```

**Node.js:**

```bash
npm install better-sqlite3
# If compilation fails, try:
npm install --save-dev --build-from-source better-sqlite3
```

---

## Exporting to Excel

Both scripts can export to Excel files automatically. The Excel files include:

- Hour-by-hour summary
- Formatted headers with blue background
- Centered numeric columns
- Auto-sized column widths

Open the `.xlsx` file in Excel, Google Sheets, or any spreadsheet application.

---

## Creating Custom Analyses

### Most Populated Hours

```sql
SELECT
    hour,
    SUM(unique_people) as total_people,
    COUNT(DISTINCT location) as instances
FROM (
    SELECT
        CAST(strftime('%H', created_at) AS INTEGER) as hour,
        COUNT(DISTINCT display_name) as unique_people,
        location
    FROM gamelog_join_leave
    WHERE DATE(created_at) = '2024-12-30'
    GROUP BY hour, location
)
GROUP BY hour
ORDER BY total_people DESC;
```

### Instance Visit Duration

```sql
SELECT
    location,
    world_name,
    SUM(time) / 3600.0 as total_hours,
    COUNT(*) as visits,
    ROUND(SUM(time) / COUNT(*) / 60.0, 1) as avg_minutes_per_visit
FROM gamelog_location
WHERE DATE(created_at) >= date('now', '-7 days')
GROUP BY location
ORDER BY total_hours DESC;
```

### Friend Activity Heatmap

```sql
SELECT
    display_name,
    CAST(strftime('%H', created_at) AS INTEGER) as hour,
    COUNT(*) as interactions
FROM gamelog_join_leave
WHERE DATE(created_at) = '2024-12-30'
GROUP BY display_name, hour
ORDER BY display_name, hour;
```

---

## Notes

- **Time Zone:** All timestamps use ISO 8601 format with UTC timezone
- **Database Backup:** Consider backing up `VRCX.sqlite3` before running scripts
- **Read-Only Access:** The scripts open the database in read-only mode to avoid accidental data loss
- **Performance:** Large datasets (weeks of data) may take a few seconds to query

---

## More Information

For detailed information about the database structure, see:

- [DATABASE_STRUCTURE_REVIEW.md](DATABASE_STRUCTURE_REVIEW.md)

For more information about VRCX:

- [VRCX GitHub Repository](https://github.com/vrcx-team/VRCX)
- [VRCX Wiki](https://github.com/vrcx-team/VRCX/wiki)
