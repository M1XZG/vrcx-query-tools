# Usage Examples

This document provides detailed examples of querying your VRCX database with various command-line options.

## Table of Contents

- [Basic Queries](#basic-queries)
- [Date Range Queries](#date-range-queries)
- [Average Attendance](#average-attendance)
- [Day of Week Analysis](#day-of-week-analysis)
- [Weekly Breakdown](#weekly-breakdown)
- [Unique Visitors Mode](#unique-visitors-mode)
- [Export Options](#export-options)
- [Common Use Cases](#common-use-cases)

## Basic Queries

### Query Today's Data

```bash
python vrcx_query.py
```

Displays today's hour-by-hour attendance summary with charts.

### Query a Specific Date

```bash
python vrcx_query.py --date 2025-12-25
```

Shows attendance data for December 25th, 2025.

## Date Range Queries

### Query Multiple Days with Daily Breakdown

```bash
# Show every day in December with hourly breakdown
python vrcx_query.py --start-date 2025-12-01 --end-date 2025-12-31

# Query a specific week
python vrcx_query.py --start-date 2025-12-20 --end-date 2025-12-27
```

This displays Date, Hour, and Number of People for each hour of each day in the range.

## Average Attendance

### Calculate Average Attendance by Hour

```bash
# Average for a date range
python vrcx_query.py --start-date 2025-12-20 --end-date 2025-12-30 --average

# Average for just one day
python vrcx_query.py --date 2025-12-25 --average
```

Shows the average number of people joining/leaving at each hour across the date range.

## Day of Week Analysis

### Average Attendance by Day of Week

```bash
# Average attendance for each day of the week (generates chart)
python vrcx_query.py --start-date 2025-12-01 --end-date 2025-12-31 --day-of-week

# Also export to CSV and Excel
python vrcx_query.py --start-date 2025-12-01 --end-date 2025-12-31 --day-of-week --export-data
```

This shows which days of the week have the highest average attendance (Sunday through Saturday), helping you identify the best days to visit. A chart is always generated and saved as a PNG image.

## Weekly Breakdown

### Week-by-Week Analysis

```bash
# Week-by-week breakdown for December (generates charts automatically)
python vrcx_query.py --start-date 2025-12-01 --end-date 2025-12-31 --weekly

# Also export data to CSV and Excel
python vrcx_query.py --start-date 2025-12-01 --end-date 2025-12-31 --weekly --export-data
```

Creates a report showing each week's attendance by day (Sunday through Saturday). Charts are automatically generated:
- A separate bar chart for each individual week
- A combined chart showing all weeks together in a single image for easy comparison

**Example Combined Weekly Chart:**

![Weekly Attendance Breakdown Example](images/weekly_breakdown_example.png)

The combined chart shows multiple weeks of attendance data with all weeks displayed in a grid layout, making it easy to compare patterns across the entire month at a glance.

## Unique Visitors Mode

### Count Unique Visitors Only Once Per Day

The `--unique` flag counts each person only once per day, regardless of how many times they joined or left the instance.

**Example:** If a user joins at 10 AM, leaves at 11 AM, and rejoins at 2 PM, they'll be counted as 1 unique visitor for the day instead of 2.

```bash
# Get unique visitor count for a specific date
python vrcx_query.py --date 2025-12-25 --unique

# Average unique visitors per hour across a date range
python vrcx_query.py --start-date 2025-12-20 --end-date 2025-12-30 --average --unique

# Unique visitors by day of week
python vrcx_query.py --start-date 2025-12-01 --end-date 2025-12-31 --day-of-week --unique

# Week-by-week unique visitor breakdown
python vrcx_query.py --start-date 2025-12-01 --end-date 2025-12-31 --weekly --unique
```

This is useful for understanding visitor traffic instead of total join/leave events.

## Export Options

### Charts vs Data Files

By default, all queries generate charts (PNG images). To also export data to CSV and Excel, use the `--export-data` flag:

```bash
# Generate chart only (default, faster)
python vrcx_query.py --start-date 2025-12-20 --end-date 2025-12-30 --average

# Generate chart and export data files
python vrcx_query.py --start-date 2025-12-20 --end-date 2025-12-30 --average --export-data
```

### Export File Formats

**Data Files (when using --export-data):**

- **CSV:**
  - Single date: `vrcx_exports/vrcx_hourly_YYYY-MM-DD.csv`
  - Date range: `vrcx_exports/vrcx_daily_YYYY-MM-DD_to_YYYY-MM-DD.csv`
  - Average: `vrcx_exports/vrcx_average_YYYY-MM-DD_to_YYYY-MM-DD.csv`
  - Day of week: `vrcx_exports/vrcx_day_of_week_YYYY-MM-DD_to_YYYY-MM-DD.csv`
  - Weekly breakdown: `vrcx_exports/vrcx_weekly_YYYY-MM-DD_to_YYYY-MM-DD.csv`

- **Excel:**
  - Single date: `vrcx_exports/vrcx_hourly_YYYY-MM-DD.xlsx`
  - Date range: `vrcx_exports/vrcx_daily_YYYY-MM-DD_to_YYYY-MM-DD.xlsx`
  - Average: `vrcx_exports/vrcx_average_YYYY-MM-DD_to_YYYY-MM-DD.xlsx`
  - Day of week: `vrcx_exports/vrcx_day_of_week_YYYY-MM-DD_to_YYYY-MM-DD.xlsx`
  - Weekly breakdown: `vrcx_exports/vrcx_weekly_YYYY-MM-DD_to_YYYY-MM-DD.xlsx`

**Charts (always generated):**

- Average attendance: `vrcx_exports/vrcx_average_YYYY-MM-DD_to_YYYY-MM-DD.png`
- Daily attendance: `vrcx_exports/vrcx_hourly_YYYY-MM-DD.png`
- Day of week: `vrcx_exports/vrcx_day_of_week_YYYY-MM-DD_to_YYYY-MM-DD.png`
- Weekly breakdown:
  - Individual weeks: `vrcx_exports/vrcx_week_YYYY-MM-DD_to_YYYY-MM-DD.png` (one per week)
  - Combined view: `vrcx_exports/vrcx_weekly_YYYY-MM-DD_to_YYYY-MM-DD_combined.png` (all weeks)

## Common Use Cases

### Find the Busiest Times

```bash
# Analyze an entire month to find peak hours
python vrcx_query.py --start-date 2025-12-01 --end-date 2025-12-31 --average
```

### Compare Weekdays vs Weekends

```bash
# See which days of the week are most active
python vrcx_query.py --start-date 2025-12-01 --end-date 2025-12-31 --day-of-week
```

### Track Growth Over Time

```bash
# Compare week-by-week attendance
python vrcx_query.py --start-date 2025-12-01 --end-date 2025-12-31 --weekly
```

### Count Actual Visitors (Not Just Join/Leave Events)

```bash
# Count unique visitors per day
python vrcx_query.py --start-date 2025-12-01 --end-date 2025-12-31 --day-of-week --unique
```

### Verbose Output for Debugging

```bash
# Show detailed database information
python vrcx_query.py --start-date 2025-12-01 --end-date 2025-12-31 --day-of-week --verbose
```

## Combining Options

You can combine most options for more complex queries:

```bash
# Unique visitors with average by hour and data export
python vrcx_query.py --start-date 2025-12-20 --end-date 2025-12-30 --average --unique --export-data

# Weekly breakdown with unique visitor count and verbose output
python vrcx_query.py --start-date 2025-12-01 --end-date 2025-12-31 --weekly --unique --verbose
```
