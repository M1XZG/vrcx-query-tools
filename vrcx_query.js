#!/usr/bin/env node
/**
 * VRCX Database Query Script (Node.js)
 *
 * Query the VRCX SQLite database and generate hour-by-hour reports
 * of VRChat instance occupancy data.
 *
 * Installation:
 *   npm install better-sqlite3
 *
 * Usage:
 *   node vrcx_query.js [date]
 *
 * Examples:
 *   node vrcx_query.js              # Today's data
 *   node vrcx_query.js 2024-12-30   # Specific date
 */

const path = require('path');
const os = require('os');
const fs = require('fs');

// Try to find the database
function findVRCXDatabase() {
    let dbPath = null;

    // Check environment variable first
    if (
        process.env.VRCX_DATABASE_PATH &&
        fs.existsSync(process.env.VRCX_DATABASE_PATH)
    ) {
        return process.env.VRCX_DATABASE_PATH;
    }

    // Windows
    if (process.platform === 'win32') {
        const appdata = process.env.APPDATA;
        if (appdata) {
            dbPath = path.join(appdata, 'VRCX', 'VRCX.sqlite3');
            if (fs.existsSync(dbPath)) {
                return dbPath;
            }
        }
    }

    // Linux/Mac
    const home = os.homedir();
    const possiblePaths = [
        path.join(home, '.config', 'VRCX', 'VRCX.sqlite3'), // Linux
        path.join(
            home,
            'Library',
            'Application Support',
            'VRCX',
            'VRCX.sqlite3'
        ) // macOS
    ];

    for (const p of possiblePaths) {
        if (fs.existsSync(p)) {
            return p;
        }
    }

    return null;
}

// ==============================================================================
// Database Initialization
// ==============================================================================

let db = null;
let Database = null;

try {
    Database = require('better-sqlite3');
} catch (e) {
    console.error('ERROR: better-sqlite3 not installed');
    console.error('Install with: npm install better-sqlite3');
    process.exit(1);
}

const DATABASE_PATH = findVRCXDatabase();

if (!DATABASE_PATH) {
    console.error('ERROR: Could not find VRCX.sqlite3 database');
    console.error('Please ensure VRCX is installed and data directory exists');
    process.exit(1);
}

console.log(`Using database: ${DATABASE_PATH}\n`);

// Connect to database
try {
    db = new Database(DATABASE_PATH, { readonly: true }); // readonly to avoid locking
    console.log('✓ Connected to database\n');
} catch (e) {
    console.error(`✗ Failed to connect: ${e.message}`);
    process.exit(1);
}

// ==============================================================================
// Query Functions
// ==============================================================================

class VRCXQuery {
    constructor(database) {
        this.db = database;
    }

    /**
     * Get location/instance history for a date
     */
    getLocationHistory(dateStr) {
        const stmt = this.db.prepare(`
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
        `);

        return stmt.all(dateStr);
    }

    /**
     * Get join/leave events for a location and date
     */
    getJoinLeaveEvents(dateStr, location = null) {
        let stmt;

        if (location) {
            stmt = this.db.prepare(`
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
            `);
            return stmt.all(location, dateStr);
        } else {
            stmt = this.db.prepare(`
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
            `);
            return stmt.all(dateStr);
        }
    }

    /**
     * Hour-by-hour summary - YOUR PRIMARY QUERY
     */
    getHourByHourSummary(dateStr) {
        const stmt = this.db.prepare(`
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
        `);

        return stmt.all(dateStr);
    }

    /**
     * Detailed people tracking by hour
     */
    getPeopleByHour(dateStr) {
        const stmt = this.db.prepare(`
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
        `);

        return stmt.all(dateStr);
    }

    /**
     * Instance statistics for a date
     */
    getInstanceStatistics(dateStr) {
        const stmt = this.db.prepare(`
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
        `);

        return stmt.all(dateStr);
    }

    /**
     * Get list of all tables
     */
    getTableNames() {
        const stmt = this.db.prepare(`
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        `);

        return stmt.all().map((row) => row.name);
    }
}

// ==============================================================================
// Reporting Functions
// ==============================================================================

function printLocationHistory(query, dateStr) {
    console.log(`\n${'='.repeat(80)}`);
    console.log(`Location History - ${dateStr}`);
    console.log(`${'='.repeat(80)}`);

    const locations = query.getLocationHistory(dateStr);

    if (locations.length === 0) {
        console.log('No location data found for this date');
        return;
    }

    for (const loc of locations) {
        const hours = (loc.duration_seconds || 0) / 3600;
        console.log(
            `[${loc.created_at}] ${loc.world_name || 'Unknown'} (${loc.location})`
        );
        console.log(
            `  Duration: ${hours.toFixed(2)} hours (${loc.duration_seconds}s)`
        );
    }
}

function printHourByHourSummary(query, dateStr) {
    console.log(`\n${'='.repeat(120)}`);
    console.log(`Hour-by-Hour Summary - ${dateStr}`);
    console.log(`${'='.repeat(120)}`);

    const summary = query.getHourByHourSummary(dateStr);

    if (summary.length === 0) {
        console.log('No data found for this date');
        return;
    }

    // Print header
    console.log(
        'Hour     Instance                           World                          Joins    Leaves   Net    People  '
    );
    console.log('-'.repeat(120));

    for (const row of summary) {
        const hour = String(row.hour).padStart(2, '0') + ':00';
        const instance = (row.location || 'Unknown')
            .substring(0, 34)
            .padEnd(34);
        const world = (row.world_name || 'Unknown').substring(0, 28).padEnd(28);
        const joins = String(row.joins || 0).padStart(7);
        const leaves = String(row.leaves || 0).padStart(7);
        const net = String(row.net_change || 0).padStart(5);
        const people = String(row.unique_people || 0).padStart(7);

        console.log(
            `${hour}     ${instance} ${world} ${joins}   ${leaves}   ${net}    ${people}`
        );
    }
}

function printInstanceStatistics(query, dateStr) {
    console.log(`\n${'='.repeat(100)}`);
    console.log(`Instance Statistics - ${dateStr}`);
    console.log(`${'='.repeat(100)}`);

    const stats = query.getInstanceStatistics(dateStr);

    if (stats.length === 0) {
        console.log('No instance data found for this date');
        return;
    }

    console.log(
        'Instance                           World                          Visits  Total Time(hrs)'
    );
    console.log('-'.repeat(100));

    for (const stat of stats) {
        const instance = (stat.location || 'Unknown')
            .substring(0, 33)
            .padEnd(33);
        const world = (stat.world_name || 'Unknown')
            .substring(0, 28)
            .padEnd(28);
        const visits = String(stat.visits).padStart(6);
        const hours = ((stat.total_time_seconds || 0) / 3600)
            .toFixed(2)
            .padStart(15);

        console.log(`${instance} ${world} ${visits}  ${hours}`);
    }
}

// ==============================================================================
// Export Functions
// ==============================================================================

function exportToCSV(query, dateStr) {
    const outputDir = './vrcx_exports';

    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    const filename = `${outputDir}/vrcx_hourly_${dateStr}.csv`;
    const summary = query.getHourByHourSummary(dateStr);

    if (summary.length === 0) {
        console.log('No data to export');
        return;
    }

    // Create CSV content
    let csv =
        'Hour,Instance,World Name,Joins,Leaves,Net Change,Unique People\n';

    for (const row of summary) {
        const hour = String(row.hour).padStart(2, '0') + ':00';
        const instance = `"${(row.location || '').replace(/"/g, '""')}"`;
        const world = `"${(row.world_name || '').replace(/"/g, '""')}"`;
        csv += `${hour},${instance},${world},${row.joins || 0},${row.leaves || 0},${row.net_change || 0},${row.unique_people || 0}\n`;
    }

    fs.writeFileSync(filename, csv);
    console.log(`✓ Exported to ${filename}`);

    return filename;
}

function exportToJSON(query, dateStr) {
    const outputDir = './vrcx_exports';

    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    const filename = `${outputDir}/vrcx_hourly_${dateStr}.json`;
    const summary = query.getHourByHourSummary(dateStr);

    if (summary.length === 0) {
        console.log('No data to export');
        return;
    }

    // Create JSON with metadata
    const data = {
        date: dateStr,
        exported_at: new Date().toISOString(),
        total_hours: summary.length,
        summary: summary
    };

    fs.writeFileSync(filename, JSON.stringify(data, null, 2));
    console.log(`✓ Exported to ${filename}`);

    return filename;
}

// ==============================================================================
// Main
// ==============================================================================

function main() {
    try {
        // Get date from command line or use today
        let dateStr = process.argv[2];
        if (!dateStr) {
            const today = new Date();
            dateStr = today.toISOString().split('T')[0];
        }

        console.log(`Querying data for: ${dateStr}\n`);

        // Initialize query helper
        const query = new VRCXQuery(db);

        // Show available tables
        console.log('Available tables:');
        const tables = query.getTableNames();
        for (const table of tables) {
            console.log(`  - ${table}`);
        }

        // Run queries
        console.log(`\n${'='.repeat(80)}`);
        console.log('QUERYING VRCX DATABASE');
        console.log(`${'='.repeat(80)}`);

        printLocationHistory(query, dateStr);
        printHourByHourSummary(query, dateStr);
        printInstanceStatistics(query, dateStr);

        // Export data
        console.log(`\n${'='.repeat(80)}`);
        console.log('EXPORTING DATA');
        console.log(`${'='.repeat(80)}`);

        exportToCSV(query, dateStr);
        exportToJSON(query, dateStr);

        console.log(`\n✓ All exports completed in ./vrcx_exports/`);
    } catch (error) {
        console.error(`\n✗ Error: ${error.message}`);
        console.error(error.stack);
        process.exit(1);
    } finally {
        if (db) {
            db.close();
            console.log('\n✓ Database connection closed');
        }
    }
}

// Run main
main();
