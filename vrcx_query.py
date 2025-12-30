#!/usr/bin/env python3
"""
VRCX Database Query Script
Demonstrates how to access the live VRCX database and analyze VRChat instance data.

This script provides examples for:
1. Connecting to the VRCX SQLite database
2. Querying location and join/leave events
3. Creating an hour-by-hour report of people in instances
4. Exporting data to CSV/Excel

Requirements:
    pip install sqlite3 pandas openpyxl
    (sqlite3 is built-in with Python)

Usage:
    python vrcx_query.py
"""

import sqlite3
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import json
import argparse

# ==============================================================================
# Configuration
# ==============================================================================

# Try to find the VRCX database automatically
def find_vrcx_database():
    """Locate the VRCX.sqlite3 database file."""
    # Windows
    if sys.platform == 'win32':
        appdata = os.getenv('APPDATA')
        if appdata:
            db_path = Path(appdata) / 'VRCX' / 'VRCX.sqlite3'
            if db_path.exists():
                return str(db_path)
    
    # Linux/Mac
    home = Path.home()
    possible_paths = [
        home / '.config' / 'VRCX' / 'VRCX.sqlite3',  # Linux
        home / 'Library' / 'Application Support' / 'VRCX' / 'VRCX.sqlite3',  # macOS
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path)
    
    return None


DATABASE_PATH = os.getenv('VRCX_DATABASE_PATH') or find_vrcx_database()

if not DATABASE_PATH:
    print("ERROR: Could not find VRCX.sqlite3 database")
    print("Please set VRCX_DATABASE_PATH environment variable or ensure VRCX is installed")
    sys.exit(1)

print(f"Using database: {DATABASE_PATH}")

# ==============================================================================
# Database Connection
# ==============================================================================

class VRCXDatabase:
    """Interface to the VRCX SQLite database."""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = None
    
    def connect(self):
        """Establish database connection."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Return rows as dictionaries
            print(f"✓ Connected to database")
        except sqlite3.Error as e:
            print(f"✗ Database connection failed: {e}")
            sys.exit(1)
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            print(f"✓ Database connection closed")
    
    def execute(self, query, params=None):
        """Execute a query and return results."""
        if not self.connection:
            self.connect()
        
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"✗ Query failed: {e}")
            print(f"Query: {query}")
            if params:
                print(f"Params: {params}")
            return []
    
    def get_table_names(self):
        """Get list of all tables in database."""
        query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        rows = self.execute(query)
        return [row['name'] for row in rows]


# ==============================================================================
# Query Functions
# ==============================================================================

class VRCXQuery:
    """Query helper for common VRCX analysis tasks."""
    
    def __init__(self, db):
        self.db = db
    
    def get_location_history(self, date_str=None):
        """
        Get your location/instance history for a specific date.
        
        Args:
            date_str: Date in format 'YYYY-MM-DD'. If None, uses today.
        
        Returns:
            List of location entries with timestamps and duration.
        """
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        query = """
        SELECT 
            id,
            created_at,
            location,
            world_id,
            world_name,
            time as duration_seconds,
            group_name
        FROM gamelog_location
        WHERE DATE(created_at) = ?
        ORDER BY created_at ASC
        """
        
        results = self.db.execute(query, (date_str,))
        return results
    
    def get_join_leave_events(self, location=None, date_str=None):
        """
        Get join/leave events for a specific location and date.
        
        Args:
            location: Instance ID (e.g., 'wrld_12345:12345~region(us)') or None for all
            date_str: Date in format 'YYYY-MM-DD'. If None, uses today.
        
        Returns:
            List of join/leave events with user info.
        """
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        if location:
            query = """
            SELECT 
                id,
                created_at,
                type,
                display_name,
                user_id,
                location,
                time
            FROM gamelog_join_leave
            WHERE location = ? AND DATE(created_at) = ?
            ORDER BY created_at ASC
            """
            results = self.db.execute(query, (location, date_str))
        else:
            query = """
            SELECT 
                id,
                created_at,
                type,
                display_name,
                user_id,
                location,
                time
            FROM gamelog_join_leave
            WHERE DATE(created_at) = ?
            ORDER BY created_at ASC
            """
            results = self.db.execute(query, (date_str,))
        
        return results
    
    def get_hour_by_hour_summary(self, date_str=None):
        """
        Get hour-by-hour summary of instances and people for a specific date.
        
        Returns data like:
        Hour | Unique People
        """
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        query = """
        SELECT 
            CAST(strftime('%H', created_at) AS INTEGER) as hour,
            COUNT(DISTINCT display_name) as unique_people
        FROM gamelog_join_leave
        WHERE DATE(created_at) = ?
        GROUP BY hour
        ORDER BY hour ASC
        """
        
        results = self.db.execute(query, (date_str,))
        return results
    
    def get_hour_by_hour_average(self, start_date_str=None, end_date_str=None):
        """
        Get average hour-by-hour attendance across a date range.
        
        Returns average data like:
        Hour | Avg Unique People
        """
        if start_date_str is None:
            start_date_str = datetime.now().strftime('%Y-%m-%d')
        if end_date_str is None:
            end_date_str = start_date_str
        
        query = """
        SELECT 
            hour,
            CAST(ROUND(AVG(unique_people)) AS INTEGER) as avg_unique_people
        FROM (
            SELECT 
                DATE(created_at) as date,
                CAST(strftime('%H', created_at) AS INTEGER) as hour,
                COUNT(DISTINCT display_name) as unique_people
            FROM gamelog_join_leave
            WHERE DATE(created_at) BETWEEN ? AND ?
            GROUP BY DATE(created_at), hour
        )
        GROUP BY hour
        ORDER BY hour ASC
        """
        
        results = self.db.execute(query, (start_date_str, end_date_str))
        return results
    
    def get_daily_hourly_summary(self, start_date_str=None, end_date_str=None):
        """
        Get hour-by-hour summary for each day in a date range.
        
        Returns data like:
        Date | Hour | Unique People
        """
        if start_date_str is None:
            start_date_str = datetime.now().strftime('%Y-%m-%d')
        if end_date_str is None:
            end_date_str = start_date_str
        
        query = """
        SELECT 
            DATE(created_at) as date,
            CAST(strftime('%H', created_at) AS INTEGER) as hour,
            COUNT(DISTINCT display_name) as unique_people
        FROM gamelog_join_leave
        WHERE DATE(created_at) BETWEEN ? AND ?
        GROUP BY DATE(created_at), hour
        ORDER BY DATE(created_at) ASC, hour ASC
        """
        
        results = self.db.execute(query, (start_date_str, end_date_str))
        return results
    
    def get_day_of_week_average(self, start_date_str=None, end_date_str=None):
        """
        Get average attendance by day of week.
        
        Returns data like:
        Day of Week | Avg Unique People
        """
        if start_date_str is None:
            start_date_str = datetime.now().strftime('%Y-%m-%d')
        if end_date_str is None:
            end_date_str = start_date_str
        
        query = """
        SELECT 
            CAST(strftime('%w', date) AS INTEGER) as day_of_week,
            ROUND(AVG(unique_people)) as avg_unique_people
        FROM (
            SELECT 
                DATE(created_at) as date,
                COUNT(DISTINCT display_name) as unique_people
            FROM gamelog_join_leave
            WHERE DATE(created_at) BETWEEN ? AND ?
            GROUP BY DATE(created_at)
        )
        GROUP BY day_of_week
        ORDER BY day_of_week
        """
        
        results = self.db.execute(query, (start_date_str, end_date_str))
        return results
    
    def get_weekly_day_of_week_breakdown(self, start_date_str=None, end_date_str=None):
        """
        Get attendance by day of week, grouped by week.
        
        Returns data like:
        Week Start | Week End | Day of Week | Unique People
        """
        if start_date_str is None:
            start_date_str = datetime.now().strftime('%Y-%m-%d')
        if end_date_str is None:
            end_date_str = start_date_str
        
        query = """
        SELECT 
            week_start,
            week_end,
            day_of_week,
            day_name,
            unique_people
        FROM (
            SELECT 
                DATE(created_at) as date,
                CAST(strftime('%w', created_at) AS INTEGER) as day_of_week,
                CASE CAST(strftime('%w', created_at) AS INTEGER)
                    WHEN 0 THEN 'Sunday'
                    WHEN 1 THEN 'Monday'
                    WHEN 2 THEN 'Tuesday'
                    WHEN 3 THEN 'Wednesday'
                    WHEN 4 THEN 'Thursday'
                    WHEN 5 THEN 'Friday'
                    WHEN 6 THEN 'Saturday'
                END as day_name,
                DATE(created_at, 'weekday 0', '-6 days') as week_start,
                DATE(created_at, 'weekday 0') as week_end,
                COUNT(DISTINCT display_name) as unique_people
            FROM gamelog_join_leave
            WHERE DATE(created_at) BETWEEN ? AND ?
            GROUP BY DATE(created_at)
        )
        GROUP BY week_start, week_end, day_of_week, day_name, date
        ORDER BY week_start, day_of_week
        """
        
        results = self.db.execute(query, (start_date_str, end_date_str))
        return results
    
    def get_people_in_instances_by_hour(self, date_str=None):
        """
        Get detailed breakdown of who was in instances hour-by-hour.
        
        This version tracks individual people across the day.
        """
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        query = """
        SELECT 
            CAST(strftime('%H', created_at) AS INTEGER) as hour,
            location,
            world_name,
            type,
            display_name,
            user_id,
            created_at
        FROM gamelog_join_leave
        WHERE DATE(created_at) = ?
        ORDER BY hour ASC, location ASC, created_at ASC
        """
        
        results = self.db.execute(query, (date_str,))
        return results
    
    def get_instance_statistics(self, date_str=None):
        """
        Get statistics about instances visited.
        """
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        query = """
        SELECT 
            location,
            world_name,
            COUNT(*) as visits,
            SUM(time) as total_time_seconds,
            MIN(created_at) as first_visit,
            MAX(created_at) as last_visit
        FROM gamelog_location
        WHERE DATE(created_at) = ?
        GROUP BY location
        ORDER BY total_time_seconds DESC
        """
        
        results = self.db.execute(query, (date_str,))
        return results


# ==============================================================================
# Reporting Functions
# ==============================================================================

def print_location_history(db, date_str=None):
    """Print location history for a date."""
    query = VRCXQuery(db)
    locations = query.get_location_history(date_str)
    
    print(f"\n{'='*80}")
    print(f"Location History - {date_str or 'Today'}")
    print(f"{'='*80}")
    
    if not locations:
        print("No location data found for this date")
        return
    
    for loc in locations:
        hours = loc['duration_seconds'] / 3600 if loc['duration_seconds'] else 0
        print(f"[{loc['created_at']}] {loc['world_name']} ({loc['location']})")
        print(f"  Duration: {hours:.2f} hours ({loc['duration_seconds']}s)")
        print()


def print_hour_by_hour_summary(db, date_str=None):
    """Print hour-by-hour summary of people in instances."""
    query = VRCXQuery(db)
    summary = query.get_hour_by_hour_summary(date_str)
    
    print(f"\n{'='*50}")
    print(f"Hour-by-Hour Summary - {date_str or 'Today'}")
    print(f"{'='*50}")
    
    if not summary:
        print("No data found for this date")
        return
    
    # Print header
    print(f"{'Hour':<6} {'People':<10}")
    print("-" * 50)
    
    for row in summary:
        hour = f"{row['hour']:02d}:00"
        people = row['unique_people'] or 0
        
        print(f"{hour:<6} {people:<10}")


def print_hour_by_hour_average(db, start_date_str=None, end_date_str=None):
    """Print average hour-by-hour attendance across a date range."""
    query = VRCXQuery(db)
    summary = query.get_hour_by_hour_average(start_date_str, end_date_str)
    
    print(f"\n{'='*50}")
    print(f"Average Attendance by Hour - {start_date_str} to {end_date_str or start_date_str}")
    print(f"{'='*50}")
    
    if not summary:
        print("No data found for this date range")
        return
    
    # Print header
    print(f"{'Hour':<6} {'Avg People':<15}")
    print("-" * 50)
    
    for row in summary:
        hour = f"{row['hour']:02d}:00"
        avg_people = row['avg_unique_people'] or 0
        
        print(f"{hour:<6} {avg_people:<15}")


def print_daily_hourly_summary(db, start_date_str=None, end_date_str=None):
    """Print hour-by-hour summary for each day in a date range."""
    query = VRCXQuery(db)
    summary = query.get_daily_hourly_summary(start_date_str, end_date_str)
    
    print(f"\n{'='*60}")
    print(f"Daily Hour-by-Hour Attendance - {start_date_str} to {end_date_str or start_date_str}")
    print(f"{'='*60}")
    
    if not summary:
        print("No data found for this date range")
        return
    
    # Print header
    print(f"{'Date':<12} {'Hour':<6} {'People':<10}")
    print("-" * 60)
    
    current_date = None
    for row in summary:
        date = row['date']
        hour = f"{row['hour']:02d}:00"
        people = row['unique_people'] or 0
        
        # Add blank line between dates for readability
        if current_date and current_date != date:
            print()
        
        print(f"{date:<12} {hour:<6} {people:<10}")
        current_date = date


def print_day_of_week_average(db, start_date_str=None, end_date_str=None):
    """Print average attendance by day of week."""
    query = VRCXQuery(db)
    summary = query.get_day_of_week_average(start_date_str, end_date_str)
    
    print(f"\n{'='*40}")
    print(f"Average Attendance by Day of Week")
    print(f"{start_date_str} to {end_date_str or start_date_str}")
    print(f"{'='*40}")
    
    if not summary:
        print("No data found for this date range")
        return
    
    # Days of week (Sunday=0 to Saturday=6 in SQLite)
    days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    # Print header
    print(f"{'Day of Week':<12} {'Avg People':<15}")
    print("-" * 40)
    
    for row in summary:
        day_name = days[row['day_of_week']]
        avg_people = row['avg_unique_people'] or 0
        
        print(f"{day_name:<12} {avg_people:<15}")


def print_weekly_day_of_week_breakdown(db, start_date_str=None, end_date_str=None):
    """Print attendance by day of week for each week in the date range."""
    query = VRCXQuery(db)
    summary = query.get_weekly_day_of_week_breakdown(start_date_str, end_date_str)
    
    if not summary:
        print("No data found for this date range")
        return
    
    print(f"\n{'='*60}")
    print(f"Weekly Breakdown by Day of Week")
    print(f"{start_date_str} to {end_date_str or start_date_str}")
    print(f"{'='*60}\n")
    
    # Group by week
    current_week = None
    for row in summary:
        week_key = (row['week_start'], row['week_end'])
        
        # Print week header when we encounter a new week
        if current_week != week_key:
            if current_week is not None:
                print()  # Blank line between weeks
            print(f"Week: {row['week_start']} to {row['week_end']}")
            print("-" * 40)
            current_week = week_key
        
        day_name = row['day_name']
        people = row['unique_people'] or 0
        print(f"  {day_name:<12} {people:>8}")
    
    print()


# ==============================================================================
# Chart Generation Functions
# ==============================================================================

def create_average_chart(db, output_file, start_date_str=None, end_date_str=None):
    """Create a bar chart showing average attendance by hour."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
    except ImportError:
        print("WARNING: matplotlib not installed. Install with: pip install matplotlib")
        return
    
    query = VRCXQuery(db)
    summary = query.get_hour_by_hour_average(start_date_str, end_date_str)
    
    if not summary:
        print("No data to chart")
        return
    
    # Extract data
    hours = [row['hour'] for row in summary]
    avg_people = [row['avg_unique_people'] or 0 for row in summary]
    
    # Create chart
    plt.figure(figsize=(10, 6))
    plt.bar(hours, avg_people, color='#1f77b4', width=0.8)
    plt.xlabel('Hour', fontsize=12)
    plt.ylabel('Average People', fontsize=12)
    plt.title('Average People by Hour', fontsize=14, fontweight='bold')
    plt.xticks(hours, [f'{h:02d}' for h in hours])
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Chart saved to {output_file}")


def create_daily_chart(db, output_file, date_str=None):
    """Create a bar chart showing hourly attendance for a specific day."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
    except ImportError:
        print("WARNING: matplotlib not installed. Install with: pip install matplotlib")
        return
    
    query = VRCXQuery(db)
    summary = query.get_hour_by_hour_summary(date_str)
    
    if not summary:
        print("No data to chart")
        return
    
    # Extract data
    hours = [row['hour'] for row in summary]
    people = [row['unique_people'] or 0 for row in summary]
    
    # Create chart
    plt.figure(figsize=(10, 6))
    plt.bar(hours, people, color='#1f77b4', width=0.8)
    plt.xlabel('Hour', fontsize=12)
    plt.ylabel('Unique People', fontsize=12)
    plt.title(f'Hourly Attendance - {date_str}', fontsize=14, fontweight='bold')
    plt.xticks(hours, [f'{h:02d}' for h in hours])
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Chart saved to {output_file}")


def create_day_of_week_chart(db, output_file, start_date_str=None, end_date_str=None):
    """Create a bar chart showing average attendance by day of week."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
    except ImportError:
        print("WARNING: matplotlib not installed. Install with: pip install matplotlib")
        return
    
    query = VRCXQuery(db)
    summary = query.get_day_of_week_average(start_date_str, end_date_str)
    
    if not summary:
        print("No data to chart")
        return
    
    # Days of week (Sunday=0 to Saturday=6 in SQLite)
    days_full = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    # Extract data
    day_indices = [row['day_of_week'] for row in summary]
    day_names = [days_full[idx] for idx in day_indices]
    avg_people = [row['avg_unique_people'] or 0 for row in summary]
    
    # Create chart
    plt.figure(figsize=(10, 6))
    plt.bar(day_names, avg_people, color='#2ca02c', width=0.6)
    plt.xlabel('Day of Week', fontsize=12)
    plt.ylabel('Average Unique People', fontsize=12)
    plt.title(f'Average Attendance by Day of Week\n{start_date_str} to {end_date_str or start_date_str}', 
              fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Chart saved to {output_file}")


def create_weekly_charts(db, output_dir, start_date_str=None, end_date_str=None):
    """Create separate bar charts for each week showing day-of-week attendance."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
    except ImportError:
        print("WARNING: matplotlib not installed. Install with: pip install matplotlib")
        return []
    
    from pathlib import Path
    query = VRCXQuery(db)
    summary = query.get_weekly_day_of_week_breakdown(start_date_str, end_date_str)
    
    if not summary:
        print("No data to chart")
        return []
    
    # Days of week for ordering
    days_full = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    # Group data by week
    weeks = {}
    for row in summary:
        week_key = (row['week_start'], row['week_end'])
        if week_key not in weeks:
            weeks[week_key] = {}
        weeks[week_key][row['day_of_week']] = row['unique_people'] or 0
    
    # Create a chart for each week
    chart_files = []
    for (week_start, week_end), week_data in sorted(weeks.items()):
        # Prepare data for this week
        day_indices = sorted(week_data.keys())
        day_names = [days_full[idx] for idx in day_indices]
        people = [week_data[idx] for idx in day_indices]
        
        # Create chart
        plt.figure(figsize=(10, 6))
        plt.bar(day_names, people, color='#ff7f0e', width=0.6)
        plt.xlabel('Day of Week', fontsize=12)
        plt.ylabel('Unique People', fontsize=12)
        plt.title(f'Weekly Attendance: {week_start} to {week_end}', 
                  fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        
        # Save chart
        output_file = Path(output_dir) / f"vrcx_week_{week_start}_to_{week_end}.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        chart_files.append(str(output_file))
        print(f"✓ Chart saved to {output_file}")
    
    return chart_files


def create_combined_weekly_chart(db, output_file, start_date_str=None, end_date_str=None):
    """Create a single combined chart with all weeks as subplots."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
    except ImportError:
        print("WARNING: matplotlib not installed. Install with: pip install matplotlib")
        return
    
    from pathlib import Path
    import math
    
    query = VRCXQuery(db)
    summary = query.get_weekly_day_of_week_breakdown(start_date_str, end_date_str)
    
    if not summary:
        print("No data to chart")
        return
    
    # Days of week for ordering
    days_full = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    # Group data by week
    weeks = {}
    for row in summary:
        week_key = (row['week_start'], row['week_end'])
        if week_key not in weeks:
            weeks[week_key] = {}
        weeks[week_key][row['day_of_week']] = row['unique_people'] or 0
    
    num_weeks = len(weeks)
    if num_weeks == 0:
        print("No weeks to chart")
        return
    
    # Calculate grid layout (prefer 2 columns, adjust rows as needed)
    cols = 2 if num_weeks > 1 else 1
    rows = math.ceil(num_weeks / cols)
    
    # Create figure with subplots
    fig, axes = plt.subplots(rows, cols, figsize=(15, 5 * rows))
    
    # Flatten axes array for easier iteration
    if num_weeks == 1:
        axes = [axes]
    else:
        axes = axes.flatten() if rows > 1 else [axes] if cols == 1 else axes
    
    # Plot each week in a subplot
    for idx, ((week_start, week_end), week_data) in enumerate(sorted(weeks.items())):
        ax = axes[idx]
        
        # Prepare data for this week
        day_indices = sorted(week_data.keys())
        day_names = [days_full[i] for i in day_indices]
        people = [week_data[i] for i in day_indices]
        
        # Create bar chart
        ax.bar(day_names, people, color='#ff7f0e', width=0.6)
        ax.set_title(f'{week_start} to {week_end}', fontsize=12, fontweight='bold')
        ax.set_xlabel('Day of Week', fontsize=10)
        ax.set_ylabel('Unique People', fontsize=10)
        ax.tick_params(axis='x', rotation=45)
        ax.grid(axis='y', alpha=0.3)
    
    # Hide any unused subplots
    for idx in range(num_weeks, len(axes)):
        axes[idx].set_visible(False)
    
    # Overall title
    fig.suptitle(f'Weekly Attendance Breakdown: {start_date_str} to {end_date_str or start_date_str}',
                 fontsize=16, fontweight='bold', y=0.995)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Combined chart saved to {output_file}")


def export_to_csv(db, output_file, date_str=None, start_date_str=None, end_date_str=None, is_average=False, is_daily=False, is_day_of_week=False, is_weekly=False):
    """Export hour-by-hour data to CSV file."""
    try:
        import csv
    except ImportError:
        print("ERROR: csv module not available")
        return
    
    query = VRCXQuery(db)
    
    if is_weekly:
        summary = query.get_weekly_day_of_week_breakdown(start_date_str, end_date_str)
        fieldnames = ['Week Start', 'Week End', 'Day of Week', 'People']
    elif is_day_of_week:
        summary = query.get_day_of_week_average(start_date_str, end_date_str)
        fieldnames = ['Day of Week', 'Avg People']
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    elif is_average:
        summary = query.get_hour_by_hour_average(start_date_str, end_date_str)
        fieldnames = ['Hour', 'Avg People']
    elif is_daily:
        summary = query.get_daily_hourly_summary(start_date_str, end_date_str)
        fieldnames = ['Date', 'Hour', 'People']
    else:
        summary = query.get_hour_by_hour_summary(date_str)
        fieldnames = ['Hour', 'People']
    
    if not summary:
        print("No data to export")
        return
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(fieldnames)
        
        for row in summary:
            if is_weekly:
                writer.writerow([
                    row['week_start'],
                    row['week_end'],
                    row['day_name'],
                    row['unique_people'] or 0
                ])
            elif is_day_of_week:
                writer.writerow([
                    days[row['day_of_week']],
                    row['avg_unique_people'] or 0
                ])
            elif is_average:
                writer.writerow([
                    f"{row['hour']:02d}:00",
                    row['avg_unique_people'] or 0
                ])
            elif is_daily:
                writer.writerow([
                    row['date'],
                    f"{row['hour']:02d}:00",
                    row['unique_people'] or 0
                ])
            else:
                writer.writerow([
                    f"{row['hour']:02d}:00",
                    row['unique_people'] or 0
                ])
    
    print(f"✓ Exported to {output_file}")


def export_to_excel(db, output_file, date_str=None, start_date_str=None, end_date_str=None, is_average=False, is_daily=False, is_day_of_week=False, is_weekly=False):
    """Export hour-by-hour data to Excel file."""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        print("WARNING: openpyxl not installed. Install with: pip install openpyxl")
        return
    
    query = VRCXQuery(db)
    
    if is_weekly:
        summary = query.get_weekly_day_of_week_breakdown(start_date_str, end_date_str)
        headers = ['Week Start', 'Week End', 'Day of Week', 'People']
    elif is_day_of_week:
        summary = query.get_day_of_week_average(start_date_str, end_date_str)
        headers = ['Day of Week', 'Avg People']
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    elif is_average:
        summary = query.get_hour_by_hour_average(start_date_str, end_date_str)
        headers = ['Hour', 'Avg People']
    elif is_daily:
        summary = query.get_daily_hourly_summary(start_date_str, end_date_str)
        headers = ['Date', 'Hour', 'People']
    else:
        summary = query.get_hour_by_hour_summary(date_str)
        headers = ['Hour', 'People']
    
    if not summary:
        print("No data to export")
        return
    
    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Hour-by-Hour"
    
    # Add headers
    ws.append(headers)
    
    # Style headers
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    # Add data rows
    for row in summary:
        if is_weekly:
            ws.append([
                row['week_start'],
                row['week_end'],
                row['day_name'],
                row['unique_people'] or 0
            ])
        elif is_day_of_week:
            ws.append([
                days[row['day_of_week']],
                row['avg_unique_people'] or 0
            ])
        elif is_average:
            ws.append([
                f"{row['hour']:02d}:00",
                row['avg_unique_people'] or 0
            ])
        elif is_daily:
            ws.append([
                row['date'],
                f"{row['hour']:02d}:00",
                row['unique_people'] or 0
            ])
        else:
            ws.append([
                f"{row['hour']:02d}:00",
                row['unique_people'] or 0
            ])
    
    # Adjust column widths
    if is_weekly:
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 12
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 12
        # Center align numeric columns
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=4, max_col=4):
            for cell in row:
                cell.alignment = Alignment(horizontal="center")
    elif is_day_of_week:
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 15
        # Center align numeric columns
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=2, max_col=2):
            for cell in row:
                cell.alignment = Alignment(horizontal="center")
    elif is_average:
        ws.column_dimensions['A'].width = 10
        ws.column_dimensions['B'].width = 15
        # Center align numeric columns
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=2, max_col=2):
            for cell in row:
                cell.alignment = Alignment(horizontal="center")
    elif is_daily:
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 10
        ws.column_dimensions['C'].width = 12
        # Center align numeric columns
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=2, max_col=3):
            for cell in row:
                cell.alignment = Alignment(horizontal="center")
    else:
        ws.column_dimensions['A'].width = 10
        ws.column_dimensions['B'].width = 15
        # Center align numeric columns
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=2, max_col=2):
            for cell in row:
                cell.alignment = Alignment(horizontal="center")
    
    wb.save(output_file)
    print(f"✓ Exported to {output_file}")


# ==============================================================================
# Main
# ==============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Query VRCX database for VRChat activity analysis')
    parser.add_argument('--date', type=str, help='Query a specific date (YYYY-MM-DD format)')
    parser.add_argument('--start-date', type=str, help='Start date for range query (YYYY-MM-DD format)')
    parser.add_argument('--end-date', type=str, help='End date for range query (YYYY-MM-DD format)')
    parser.add_argument('--average', action='store_true', help='Calculate average attendance across date range')
    parser.add_argument('--day-of-week', action='store_true', help='Show average attendance by day of week (Monday-Sunday)')
    parser.add_argument('--weekly', action='store_true', help='Show week-by-week breakdown with day-of-week attendance')
    parser.add_argument('--no-export', action='store_true', help='Skip exporting to CSV and Excel')
    parser.add_argument('--chart', action='store_true', help='Generate chart visualization (PNG)')
    
    args = parser.parse_args()
    
    # Determine dates to query
    is_date_range = args.start_date and args.end_date
    
    if args.weekly:
        if not args.start_date:
            args.start_date = datetime.now().strftime('%Y-%m-%d')
        if not args.end_date:
            args.end_date = args.start_date
    elif args.day_of_week:
        if not args.start_date:
            args.start_date = datetime.now().strftime('%Y-%m-%d')
        if not args.end_date:
            args.end_date = args.start_date
    elif args.average:
        if not args.start_date:
            args.start_date = datetime.now().strftime('%Y-%m-%d')
        if not args.end_date:
            args.end_date = args.start_date
    elif is_date_range:
        # Date range without average = daily breakdown
        pass
    else:
        if not args.date:
            args.date = datetime.now().strftime('%Y-%m-%d')
    
    # Connect to database
    db = VRCXDatabase(DATABASE_PATH)
    db.connect()
    
    try:
        # Show available tables
        print(f"\nAvailable tables:")
        tables = db.get_table_names()
        for table in tables:
            print(f"  - {table}")
        
        # Run queries
        print("\n" + "="*80)
        print("QUERYING VRCX DATABASE")
        print("="*80)
        
        if args.weekly:
            print_weekly_day_of_week_breakdown(db, args.start_date, args.end_date)
        elif args.day_of_week:
            print_day_of_week_average(db, args.start_date, args.end_date)
        elif args.average:
            print_hour_by_hour_average(db, args.start_date, args.end_date)
        elif is_date_range:
            print_daily_hourly_summary(db, args.start_date, args.end_date)
        else:
            print_location_history(db, args.date)
            print_hour_by_hour_summary(db, args.date)
        
        # Export to files
        if not args.no_export:
            print(f"\n{'='*80}")
            print("EXPORTING DATA")
            print(f"{'='*80}")
            
            output_dir = Path("./vrcx_exports")
            output_dir.mkdir(exist_ok=True)
            
            if args.weekly:
                filename_base = f"vrcx_weekly_{args.start_date}_to_{args.end_date}"
                csv_file = output_dir / f"{filename_base}.csv"
                xlsx_file = output_dir / f"{filename_base}.xlsx"
                
                export_to_csv(db, str(csv_file), start_date_str=args.start_date, 
                             end_date_str=args.end_date, is_weekly=True)
                export_to_excel(db, str(xlsx_file), start_date_str=args.start_date, 
                               end_date_str=args.end_date, is_weekly=True)
                
                # Generate charts if requested (one per week)
                if args.chart:
                    # Create individual weekly charts
                    chart_files = create_weekly_charts(db, str(output_dir), args.start_date, args.end_date)
                    print(f"✓ Created {len(chart_files)} individual weekly charts")
                    
                    # Create combined chart with all weeks
                    combined_chart = output_dir / f"{filename_base}_combined.png"
                    create_combined_weekly_chart(db, str(combined_chart), args.start_date, args.end_date)
                
            elif args.day_of_week:
                filename_base = f"vrcx_day_of_week_{args.start_date}_to_{args.end_date}"
                csv_file = output_dir / f"{filename_base}.csv"
                xlsx_file = output_dir / f"{filename_base}.xlsx"
                
                export_to_csv(db, str(csv_file), start_date_str=args.start_date, 
                             end_date_str=args.end_date, is_day_of_week=True)
                export_to_excel(db, str(xlsx_file), start_date_str=args.start_date, 
                               end_date_str=args.end_date, is_day_of_week=True)
                
                # Generate chart if requested
                if args.chart:
                    chart_file = output_dir / f"{filename_base}.png"
                    create_day_of_week_chart(db, str(chart_file), args.start_date, args.end_date)
                
            elif args.average:
                filename_base = f"vrcx_average_{args.start_date}_to_{args.end_date}"
                csv_file = output_dir / f"{filename_base}.csv"
                xlsx_file = output_dir / f"{filename_base}.xlsx"
                
                export_to_csv(db, str(csv_file), start_date_str=args.start_date, 
                             end_date_str=args.end_date, is_average=True)
                export_to_excel(db, str(xlsx_file), start_date_str=args.start_date, 
                               end_date_str=args.end_date, is_average=True)
                
                # Generate chart if requested
                if args.chart:
                    chart_file = output_dir / f"{filename_base}.png"
                    create_average_chart(db, str(chart_file), args.start_date, args.end_date)
                    
            elif is_date_range:
                filename_base = f"vrcx_daily_{args.start_date}_to_{args.end_date}"
                csv_file = output_dir / f"{filename_base}.csv"
                xlsx_file = output_dir / f"{filename_base}.xlsx"
                
                export_to_csv(db, str(csv_file), start_date_str=args.start_date, 
                             end_date_str=args.end_date, is_daily=True)
                export_to_excel(db, str(xlsx_file), start_date_str=args.start_date, 
                               end_date_str=args.end_date, is_daily=True)
            else:
                csv_file = output_dir / f"vrcx_hourly_{args.date}.csv"
                xlsx_file = output_dir / f"vrcx_hourly_{args.date}.xlsx"
                
                export_to_csv(db, str(csv_file), args.date)
                export_to_excel(db, str(xlsx_file), args.date)
                
                # Generate chart if requested
                if args.chart:
                    chart_file = output_dir / f"vrcx_hourly_{args.date}.png"
                    create_daily_chart(db, str(chart_file), args.date)
            
            print(f"\n✓ All exports completed in {output_dir}/")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == '__main__':
    main()
