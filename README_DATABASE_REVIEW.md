# VRCX Database Review - Complete Index

## 📋 Overview

This directory contains a comprehensive review of the VRCX database structure and tools to query it for VRChat activity analysis.

**Your Goal:** Create a spreadsheet showing hour-by-hour people counts in your VRChat instances  
**Status:** ✅ **Complete** - All tools and documentation provided

---

## 📚 Documentation Files

### 🎯 [DATABASE_REVIEW_SUMMARY.md](DATABASE_REVIEW_SUMMARY.md) - **START HERE**

**What it is:** Executive summary of the entire review  
**Contains:**

- Quick overview of database structure
- Summary of what I found
- List of all created files
- Quick start instructions (3 steps)
- Your specific use case explained
- Troubleshooting guide

**Read this first** if you want a quick overview.

---

### 📖 [VRCX_QUERY_GUIDE.md](VRCX_QUERY_GUIDE.md) - **PRACTICAL GUIDE**

**What it is:** Step-by-step guide to using the query tools  
**Contains:**

- Python script installation and usage
- Node.js script installation and usage
- Understanding the output format
- Troubleshooting database locks
- Setting environment variables
- Custom query examples
- Advanced usage patterns

**Read this** when you're ready to run the scripts.

---

### 🗂️ [DATABASE_STRUCTURE_REVIEW.md](DATABASE_STRUCTURE_REVIEW.md) - **TECHNICAL REFERENCE**

**What it is:** Complete technical documentation of all tables  
**Contains:**

- Detailed schema for 20+ tables
- Column descriptions and data types
- User-specific vs. global tables
- Data retention policies
- Timestamp and location formats
- Connection details
- Code references

**Read this** when you need to understand the complete structure.

---

### 📊 [DATABASE_SCHEMA_DIAGRAM.md](DATABASE_SCHEMA_DIAGRAM.md) - **VISUAL REFERENCE**

**What it is:** Visual diagrams and relationship maps  
**Contains:**

- High-level architecture diagram
- Entity relationship diagrams
- Table hierarchy and organization
- Query flow diagrams
- Data flow through VRCX
- Timestamp and location formats
- Table size reference

**Read this** if you prefer visual explanations.

---

## 🛠️ Query Tools & Scripts

### 🐍 [vrcx_query.py](vrcx_query.py) - **PYTHON SCRIPT (Recommended)**

**What it is:** Production-ready Python script for database analysis  
**Features:**

- Automatic database detection
- Hour-by-hour summary queries
- Location history tracking
- Instance statistics
- CSV export
- Excel export with formatting
- ~400 lines of documented code

**How to use:**

```bash
# Installation
pip install pandas openpyxl

# Usage
python vrcx_query.py              # Today's data
python vrcx_query.py 2024-12-30   # Specific date
```

**Output:**

- Console: Formatted tables
- `vrcx_exports/vrcx_hourly_YYYY-MM-DD.csv` - CSV file
- `vrcx_exports/vrcx_hourly_YYYY-MM-DD.xlsx` - Excel file

---

### 🟢 [vrcx_query.js](vrcx_query.js) - **NODE.JS SCRIPT**

**What it is:** JavaScript equivalent of Python script  
**Features:**

- Same functionality as Python version
- Automatic database detection
- Multiple output views
- CSV and JSON exports
- ~450 lines of documented code

**How to use:**

```bash
# Installation
npm install better-sqlite3

# Usage
node vrcx_query.js              # Today's data
node vrcx_query.js 2024-12-30   # Specific date
```

**Output:**

- Console: Formatted tables
- `vrcx_exports/vrcx_hourly_YYYY-MM-DD.csv` - CSV file
- `vrcx_exports/vrcx_hourly_YYYY-MM-DD.json` - JSON file

---

### 📝 [vrcx_queries.sql](vrcx_queries.sql) - **SQL QUERY LIBRARY**

**What it is:** 15+ pre-written SQL queries for direct database access  
**Queries included:**

**Primary Queries (Your Use Case):**

1. Hour-by-hour people count (main query)
2. Your location timeline
3. Join/leave timeline details

**Analysis Queries:** 4. Busiest hours 5. Most popular instances 6. Most active friends 7. Instance visit duration statistics 8. Friend interaction heatmap 9. Location transitions

**Advanced Queries:** 10. Hourly rollup 11. Cumulative people analysis 12. Time series analysis 13. Data quality checks 14. Recent 7-day summary 15. Friend presence patterns

**How to use:**

```bash
# Run all queries
sqlite3 /path/to/VRCX.sqlite3 < vrcx_queries.sql

# Or use interactively
sqlite3 /path/to/VRCX.sqlite3
sqlite> .read vrcx_queries.sql
```

---

## 🚀 Quick Start

### The 3-Step Quick Start

#### Step 1: Close VRCX Application

Database will be locked while VRCX is running.

#### Step 2: Run a Script

**Choose one option:**

**Option A - Python (Easiest):**

```bash
pip install pandas openpyxl
python vrcx_query.py
```

**Option B - Node.js:**

```bash
npm install better-sqlite3
node vrcx_query.js
```

**Option C - Direct SQL:**

```bash
sqlite3 VRCX.sqlite3 < vrcx_queries.sql
```

#### Step 3: Review Your Spreadsheet

- Open the Excel file: `vrcx_exports/vrcx_hourly_YYYY-MM-DD.xlsx`
- View the hour-by-hour summary with:
    - Time of day
    - Instance names
    - World names
    - Join count
    - Leave count
    - Unique people count

---

## 📊 Your Specific Use Case

### Goal

Create a spreadsheet showing hour-by-hour count of people in the same VRChat instances with you.

### Solution

The two critical tables are:

**1. gamelog_location**

- Tracks when you changed instances
- Shows your location timeline

**2. gamelog_join_leave**

- Records every person joining/leaving your instance
- Includes timestamp, person name, join/leave type

### The Core Query

```sql
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
```

### Sample Output

```
Hour   Instance                   World        Joins  Leaves  Unique People
12:00  wrld_abc123:123~region(us) Home            5       2           7
13:00  wrld_abc123:123~region(us) Home            2       1           8
14:00  wrld_xyz456:456~region(eu) Social Hub      8       3          12
```

Both Python and Node.js scripts automatically generate Excel files with this exact format.

---

## 🔍 File Navigation Guide

### If you want to...

**...quickly understand what's available**
→ Read [DATABASE_REVIEW_SUMMARY.md](DATABASE_REVIEW_SUMMARY.md)

**...get started immediately**
→ Follow [VRCX_QUERY_GUIDE.md](VRCX_QUERY_GUIDE.md)

**...understand the database in detail**
→ Reference [DATABASE_STRUCTURE_REVIEW.md](DATABASE_STRUCTURE_REVIEW.md)

**...see visual relationships**
→ Look at [DATABASE_SCHEMA_DIAGRAM.md](DATABASE_SCHEMA_DIAGRAM.md)

**...query data with Python**
→ Use [vrcx_query.py](vrcx_query.py)

**...query data with Node.js**
→ Use [vrcx_query.js](vrcx_query.js)

**...write custom SQL queries**
→ Reference [vrcx_queries.sql](vrcx_queries.sql)

---

## 📦 What I Found

### Database Overview

- **Type:** SQLite 3
- **Location:** `%APPDATA%\VRCX\VRCX.sqlite3` (Windows)
- **Size:** 50KB - 1MB per day of activity
- **Tables:** 20+ tables across multiple categories

### Key Tables

- ✅ `gamelog_location` - Your location timeline (CRITICAL)
- ✅ `gamelog_join_leave` - People events (CRITICAL)
- ✅ `gamelog_portal_spawn` - Portal events
- ✅ `gamelog_video_play` - Video player events
- ✅ `{userPrefix}_feed_*` - Friend activity feeds
- ✅ `{userPrefix}_friend_log_*` - Friend tracking
- ✅ `cache_avatar` / `cache_world` - Metadata caches
- ✅ `favorite_*` - User favorites
- ✅ `memos` - User notes

### Data Retention

- Game logs: Indefinitely
- Feed tables: 24-hour rolling window (default)
- Timestamps: ISO 8601 format with UTC timezone

---

## 🎯 Key Features

### What You Can Do

1. **Hour-by-hour analysis**
    - See how many people were in each instance per hour
    - Track your location changes throughout the day
    - Export to Excel for further analysis

2. **Friend analytics**
    - Identify which friends were active when
    - See patterns in friend activity
    - Track friend join/leave events

3. **Instance statistics**
    - Time spent per instance/world
    - Most popular instances by hour
    - Busiest times of day

4. **Export options**
    - CSV for Excel/Google Sheets
    - Excel with formatting
    - JSON for programmatic use

5. **Custom queries**
    - Write SQL directly against the database
    - Reference 15+ example queries
    - Create custom analyses

---

## 🔧 Technical Details

### Database Connection

- **Engine:** SQLite 3
- **Pragmas:** WAL mode, optimized for concurrency
- **Access:** Read-only (scripts won't modify data)
- **Timeout:** 5-second timeout for busy database

### Timestamp Format

- **Standard:** ISO 8601 (YYYY-MM-DDTHH:MM:SS.sssZ)
- **Timezone:** UTC
- **Parseable in:** Python, JavaScript, SQLite

### Location Format

- **Pattern:** `wrld_[world_id]:[instance_id]~region([region])`
- **Example:** `wrld_12345abcd:12345~region(us)`

---

## ⚠️ Important Notes

### Before Running Scripts

1. **Close VRCX application** - Database is locked while running
2. **Backup VRCX.sqlite3** - Just in case (scripts are read-only)
3. **Ensure database exists** - Located in `%APPDATA%\VRCX\VRCX.sqlite3`

### Troubleshooting

- **Database locked:** Close VRCX and try again
- **Database not found:** Check `%APPDATA%\VRCX\` folder
- **Missing dependencies:** `pip install pandas openpyxl` or `npm install better-sqlite3`
- **No data for date:** VRCX must have been running on that date

---

## 📞 Support Resources

### Included in This Review

- Complete database documentation
- Working Python and Node.js scripts
- 15+ ready-to-use SQL queries
- Quick start guide
- Troubleshooting guide
- Schema diagrams

### External Resources

- [VRCX GitHub Repository](https://github.com/vrcx-team/VRCX)
- [VRCX Wiki](https://github.com/vrcx-team/VRCX/wiki)
- SQLite Documentation: [www.sqlite.org](https://www.sqlite.org)

---

## ✅ Checklist

Before you start:

- [ ] I have VRCX installed
- [ ] I know where my VRCX.sqlite3 database is located
- [ ] I can close the VRCX application
- [ ] I have Python 3.6+ or Node.js 12+ installed

After setup:

- [ ] I've read the quick start in this file
- [ ] I've chosen Python or Node.js script
- [ ] I've installed required dependencies
- [ ] I've run the script successfully
- [ ] I've opened the Excel export file

---

## 📈 Next Steps

1. **Start:** Read [VRCX_QUERY_GUIDE.md](VRCX_QUERY_GUIDE.md)
2. **Install:** Follow Python or Node.js setup
3. **Run:** Execute your chosen script
4. **Analyze:** Open the Excel file with your data
5. **Explore:** Use SQL queries for custom analysis
6. **Learn:** Reference [DATABASE_STRUCTURE_REVIEW.md](DATABASE_STRUCTURE_REVIEW.md) for details

---

## 📝 File Summary Table

| File                                                         | Purpose          | Read Time | Use Case                    |
| ------------------------------------------------------------ | ---------------- | --------- | --------------------------- |
| [DATABASE_REVIEW_SUMMARY.md](DATABASE_REVIEW_SUMMARY.md)     | Overview         | 5 min     | Quick understanding         |
| [VRCX_QUERY_GUIDE.md](VRCX_QUERY_GUIDE.md)                   | Instructions     | 10 min    | Getting started             |
| [DATABASE_STRUCTURE_REVIEW.md](DATABASE_STRUCTURE_REVIEW.md) | Technical docs   | 30 min    | Deep dive                   |
| [DATABASE_SCHEMA_DIAGRAM.md](DATABASE_SCHEMA_DIAGRAM.md)     | Visual reference | 15 min    | Understanding relationships |
| [vrcx_query.py](vrcx_query.py)                               | Python tool      | -         | Main analysis               |
| [vrcx_query.js](vrcx_query.js)                               | JavaScript tool  | -         | Alternative analysis        |
| [vrcx_queries.sql](vrcx_queries.sql)                         | SQL reference    | 15 min    | Custom queries              |

---

## 🎉 Summary

You now have **everything** needed to:

1. ✅ Understand the VRCX database structure
2. ✅ Query the live database while running
3. ✅ Generate hour-by-hour people count reports
4. ✅ Export data to Excel spreadsheets
5. ✅ Create custom analyses

**Most importantly:** The Python and Node.js scripts do all the hard work for you. Just run them and you'll get your spreadsheet!

---

**Questions?** Check [VRCX_QUERY_GUIDE.md](VRCX_QUERY_GUIDE.md) troubleshooting section or reference [DATABASE_STRUCTURE_REVIEW.md](DATABASE_STRUCTURE_REVIEW.md) for technical details.

**Ready to start?** Go to [VRCX_QUERY_GUIDE.md](VRCX_QUERY_GUIDE.md) now!
