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
        Get hour-by-hour summary of instances and people.
        
        THIS IS YOUR PRIMARY QUERY FOR THE SPREADSHEET
        
        Returns data like:
        Hour | Instance | World Name | People Joined | People Left | Net Change
        """
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        query = """
        SELECT 
            CAST(strftime('%H', created_at) AS INTEGER) as hour,
            location,
            world_name,
            SUM(CASE WHEN type = 'join' THEN 1 ELSE 0 END) as joins,
            SUM(CASE WHEN type = 'leave' THEN 1 ELSE 0 END) as leaves,
            SUM(CASE WHEN type = 'join' THEN 1 ELSE -1 END) as net_change,
            COUNT(DISTINCT display_name) as unique_people
        FROM gamelog_join_leave
        WHERE DATE(created_at) = ?
        GROUP BY hour, location
        ORDER BY hour ASC, location ASC
        """
        
        results = self.db.execute(query, (date_str,))
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
    
    print(f"\n{'='*120}")
    print(f"Hour-by-Hour Summary - {date_str or 'Today'}")
    print(f"{'='*120}")
    
    if not summary:
        print("No data found for this date")
        return
    
    # Print header
    print(f"{'Hour':<6} {'Instance':<35} {'World':<30} {'Joins':<8} {'Leaves':<8} {'Net':<6} {'People':<8}")
    print("-" * 120)
    
    for row in summary:
        hour = f"{row['hour']:02d}:00"
        instance = row['location'][:34] if row['location'] else 'Unknown'
        world = row['world_name'][:28] if row['world_name'] else 'Unknown'
        joins = row['joins'] or 0
        leaves = row['leaves'] or 0
        net = row['net_change'] or 0
        people = row['unique_people'] or 0
        
        print(f"{hour:<6} {instance:<35} {world:<30} {joins:<8} {leaves:<8} {net:<6} {people:<8}")


def export_to_csv(db, output_file, date_str=None):
    """Export hour-by-hour data to CSV file."""
    try:
        import csv
    except ImportError:
        print("ERROR: csv module not available")
        return
    
    query = VRCXQuery(db)
    summary = query.get_hour_by_hour_summary(date_str)
    
    if not summary:
        print("No data to export")
        return
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Hour', 'Instance', 'World Name', 'Joins', 'Leaves', 'Net Change', 'Unique People'])
        
        for row in summary:
            writer.writerow([
                f"{row['hour']:02d}:00",
                row['location'] or '',
                row['world_name'] or '',
                row['joins'] or 0,
                row['leaves'] or 0,
                row['net_change'] or 0,
                row['unique_people'] or 0
            ])
    
    print(f"✓ Exported to {output_file}")


def export_to_excel(db, output_file, date_str=None):
    """Export hour-by-hour data to Excel file."""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        print("WARNING: openpyxl not installed. Install with: pip install openpyxl")
        return
    
    query = VRCXQuery(db)
    summary = query.get_hour_by_hour_summary(date_str)
    
    if not summary:
        print("No data to export")
        return
    
    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Hour-by-Hour"
    
    # Add headers
    headers = ['Hour', 'Instance', 'World Name', 'Joins', 'Leaves', 'Net Change', 'Unique People']
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
        ws.append([
            f"{row['hour']:02d}:00",
            row['location'] or '',
            row['world_name'] or '',
            row['joins'] or 0,
            row['leaves'] or 0,
            row['net_change'] or 0,
            row['unique_people'] or 0
        ])
    
    # Adjust column widths
    ws.column_dimensions['A'].width = 10
    ws.column_dimensions['B'].width = 40
    ws.column_dimensions['C'].width = 35
    ws.column_dimensions['D'].width = 10
    ws.column_dimensions['E'].width = 10
    ws.column_dimensions['F'].width = 12
    ws.column_dimensions['G'].width = 15
    
    # Center align numeric columns
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=4, max_col=7):
        for cell in row:
            cell.alignment = Alignment(horizontal="center")
    
    wb.save(output_file)
    print(f"✓ Exported to {output_file}")


# ==============================================================================
# Main
# ==============================================================================

def main():
    """Main entry point."""
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
        
        # Get today's data
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Show location history
        print_location_history(db, today)
        
        # Show hour-by-hour summary
        print_hour_by_hour_summary(db, today)
        
        # Export to files
        print(f"\n{'='*80}")
        print("EXPORTING DATA")
        print(f"{'='*80}")
        
        output_dir = Path("./vrcx_exports")
        output_dir.mkdir(exist_ok=True)
        
        csv_file = output_dir / f"vrcx_hourly_{today}.csv"
        export_to_csv(db, str(csv_file), today)
        
        xlsx_file = output_dir / f"vrcx_hourly_{today}.xlsx"
        export_to_excel(db, str(xlsx_file), today)
        
        print(f"\n✓ All exports completed in {output_dir}/")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == '__main__':
    main()
