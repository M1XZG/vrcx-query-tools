-- ============================================================================
-- VRCX Database Query Examples
-- ============================================================================
-- These queries can be run directly against the VRCX.sqlite3 database
-- using any SQLite client (DB Browser, sqlite3 CLI, etc.)
--
-- Usage:
--   sqlite3 /path/to/VRCX.sqlite3 < vrcx_queries.sql
--   OR
--   sqlite3 /path/to/VRCX.sqlite3
--   sqlite> .read vrcx_queries.sql
-- ============================================================================

-- ============================================================================
-- PRIMARY QUERIES - For Your Use Case
-- ============================================================================

-- 1. HOUR-BY-HOUR PEOPLE COUNT (Main Query)
-- Shows for each hour: how many people joined, left, and total unique people
-- This is ideal for creating your hour-by-hour spreadsheet
-- ============================================================================
SELECT 
    CAST(strftime('%H', created_at) AS INTEGER) as hour,
    PRINTF('%02d:00', CAST(strftime('%H', created_at) AS INTEGER)) as time_slot,
    location,
    world_name,
    SUM(CASE WHEN type = 'join' THEN 1 ELSE 0 END) as people_joined,
    SUM(CASE WHEN type = 'leave' THEN 1 ELSE 0 END) as people_left,
    SUM(CASE WHEN type = 'join' THEN 1 ELSE -1 END) as net_change,
    COUNT(DISTINCT display_name) as unique_people_this_hour
FROM gamelog_join_leave
WHERE DATE(created_at) = DATE('now')  -- Change 'now' to specific date
GROUP BY hour, location
ORDER BY hour ASC, unique_people_this_hour DESC;

-- ============================================================================
-- 2. YOUR LOCATION TIMELINE
-- Shows where you were and for how long
-- ============================================================================
SELECT 
    DATETIME(created_at) as when_changed,
    location,
    world_name,
    time as duration_seconds,
    PRINTF('%d:%02d', time / 3600, (time % 3600) / 60) as duration_display,
    group_name
FROM gamelog_location
WHERE DATE(created_at) = DATE('now')  -- Change 'now' to specific date
ORDER BY created_at ASC;

-- ============================================================================
-- 3. PEOPLE JOIN/LEAVE TIMELINE
-- Detailed timeline of when people joined and left specific instances
-- ============================================================================
SELECT 
    DATETIME(created_at) as when_event_occurred,
    PRINTF('%02d:00', CAST(strftime('%H', created_at) AS INTEGER)) as hour,
    type as event_type,
    display_name as person,
    user_id,
    location as instance,
    world_name
FROM gamelog_join_leave
WHERE DATE(created_at) = DATE('now')  -- Change 'now' to specific date
ORDER BY created_at ASC;

-- ============================================================================
-- ANALYSIS QUERIES - Insights and Patterns
-- ============================================================================

-- 4. BUSIEST HOURS (Most people overall)
-- ============================================================================
SELECT 
    PRINTF('%02d:00', hour) as time_slot,
    SUM(unique_people) as total_unique_people,
    COUNT(DISTINCT location) as different_instances,
    ROUND(AVG(unique_people), 1) as avg_per_instance
FROM (
    SELECT 
        CAST(strftime('%H', created_at) AS INTEGER) as hour,
        location,
        COUNT(DISTINCT display_name) as unique_people
    FROM gamelog_join_leave
    WHERE DATE(created_at) = DATE('now')
    GROUP BY hour, location
)
GROUP BY hour
ORDER BY total_unique_people DESC;

-- 5. MOST POPULAR INSTANCES
-- ============================================================================
SELECT 
    location,
    world_name,
    COUNT(DISTINCT display_name) as total_unique_people,
    SUM(CASE WHEN type = 'join' THEN 1 ELSE 0 END) as total_joins,
    SUM(CASE WHEN type = 'leave' THEN 1 ELSE 0 END) as total_leaves
FROM gamelog_join_leave
WHERE DATE(created_at) = DATE('now')
GROUP BY location
ORDER BY total_unique_people DESC;

-- 6. MOST ACTIVE FRIENDS (By interaction count)
-- ============================================================================
SELECT 
    display_name,
    user_id,
    COUNT(*) as total_events,
    SUM(CASE WHEN type = 'join' THEN 1 ELSE 0 END) as joined_count,
    SUM(CASE WHEN type = 'leave' THEN 1 ELSE 0 END) as left_count,
    COUNT(DISTINCT location) as different_instances
FROM gamelog_join_leave
WHERE DATE(created_at) = DATE('now')
GROUP BY user_id
ORDER BY total_events DESC
LIMIT 20;

-- 7. INSTANCE TIMELINE (Where you spent time)
-- ============================================================================
SELECT 
    DATETIME(created_at) as time_changed,
    location,
    world_name,
    time as duration_seconds,
    PRINTF('%d:%02d:%02d', 
        time / 3600, 
        (time % 3600) / 60, 
        time % 60) as duration_formatted
FROM gamelog_location
WHERE DATE(created_at) = DATE('now')
ORDER BY created_at ASC;

-- 8. FRIEND INTERACTION HEATMAP (When you see specific people)
-- ============================================================================
SELECT 
    CAST(strftime('%H', created_at) AS INTEGER) as hour,
    display_name,
    COUNT(*) as interaction_count,
    GROUP_CONCAT(type, ',') as event_types
FROM gamelog_join_leave
WHERE DATE(created_at) = DATE('now')
GROUP BY hour, display_name
ORDER BY hour, interaction_count DESC;

-- ============================================================================
-- TIME SERIES ANALYSIS
-- ============================================================================

-- 9. HOURLY ROLLUP (Simple version)
-- ============================================================================
SELECT 
    PRINTF('%02d:00', CAST(strftime('%H', created_at) AS INTEGER)) as hour,
    COUNT(CASE WHEN type = 'join' THEN 1 END) as joins,
    COUNT(CASE WHEN type = 'leave' THEN 1 END) as leaves,
    COUNT(DISTINCT display_name) as unique_people
FROM gamelog_join_leave
WHERE DATE(created_at) = DATE('now')
GROUP BY strftime('%H', created_at)
ORDER BY hour;

-- 10. CUMULATIVE PEOPLE IN INSTANCES BY HOUR
-- Shows how many people accumulated in each hour
-- ============================================================================
WITH hourly_events AS (
    SELECT 
        CAST(strftime('%H', created_at) AS INTEGER) as hour,
        location,
        type,
        COUNT(DISTINCT display_name) as count
    FROM gamelog_join_leave
    WHERE DATE(created_at) = DATE('now')
    GROUP BY hour, location, type
)
SELECT 
    hour,
    location,
    SUM(CASE WHEN type = 'join' THEN count ELSE 0 END) as joins,
    SUM(CASE WHEN type = 'leave' THEN count ELSE 0 END) as leaves,
    SUM(CASE WHEN type = 'join' THEN count ELSE -count END) as net_people
FROM hourly_events
GROUP BY hour, location
ORDER BY hour, location;

-- ============================================================================
-- DATA QUALITY & STATISTICS
-- ============================================================================

-- 11. DATA COVERAGE CHECK
-- ============================================================================
SELECT 
    'gamelog_location' as table_name,
    COUNT(*) as record_count,
    MIN(created_at) as earliest_record,
    MAX(created_at) as latest_record,
    COUNT(DISTINCT DATE(created_at)) as days_of_data
FROM gamelog_location
UNION ALL
SELECT 
    'gamelog_join_leave',
    COUNT(*),
    MIN(created_at),
    MAX(created_at),
    COUNT(DISTINCT DATE(created_at))
FROM gamelog_join_leave;

-- 12. RECENT 7 DAYS SUMMARY
-- ============================================================================
SELECT 
    DATE(created_at) as date,
    COUNT(DISTINCT location) as instances_visited,
    COUNT(DISTINCT display_name) as unique_people_seen,
    SUM(CASE WHEN type = 'join' THEN 1 ELSE 0 END) as total_joins
FROM gamelog_join_leave
WHERE created_at >= datetime('now', '-7 days')
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- ============================================================================
-- ADVANCED ANALYSIS
-- ============================================================================

-- 13. INSTANCE VISIT DURATION STATISTICS
-- ============================================================================
SELECT 
    location,
    world_name,
    COUNT(*) as visits,
    SUM(time) as total_seconds,
    ROUND(SUM(time) / 3600.0, 2) as total_hours,
    ROUND(AVG(time) / 60.0, 1) as avg_minutes_per_visit,
    ROUND(MAX(time) / 60.0, 1) as max_duration_minutes,
    ROUND(MIN(time) / 60.0, 1) as min_duration_minutes
FROM gamelog_location
WHERE created_at >= datetime('now', '-30 days')
GROUP BY location
ORDER BY total_hours DESC;

-- 14. FRIEND PRESENCE PATTERN (Who shows up when)
-- ============================================================================
SELECT 
    display_name,
    PRINTF('%02d:00', CAST(strftime('%H', created_at) AS INTEGER)) as preferred_hours,
    COUNT(*) as event_count,
    COUNT(DISTINCT DATE(created_at)) as days_active
FROM gamelog_join_leave
WHERE created_at >= datetime('now', '-14 days')
GROUP BY display_name, strftime('%H', created_at)
HAVING COUNT(*) >= 2
ORDER BY display_name, preferred_hours;

-- 15. LOCATION TRANSITIONS (Where you went)
-- ============================================================================
WITH location_sequence AS (
    SELECT 
        created_at,
        location,
        world_name,
        LAG(location) OVER (ORDER BY created_at) as previous_location,
        LAG(world_name) OVER (ORDER BY created_at) as previous_world_name
    FROM gamelog_location
    WHERE DATE(created_at) = DATE('now')
)
SELECT 
    DATETIME(created_at) as time,
    previous_world_name as from_world,
    world_name as to_world,
    previous_location as from_location,
    location as to_location
FROM location_sequence
WHERE previous_location IS NOT NULL
ORDER BY created_at ASC;

-- ============================================================================
-- EXPORT-READY QUERIES
-- ============================================================================

-- 16. CSV-FRIENDLY: Hour-by-Hour Report
-- ============================================================================
.mode csv
.output hourly_report.csv
SELECT 
    PRINTF('%02d:00', CAST(strftime('%H', created_at) AS INTEGER)) as hour,
    location,
    world_name,
    SUM(CASE WHEN type = 'join' THEN 1 ELSE 0 END) as joins,
    SUM(CASE WHEN type = 'leave' THEN 1 ELSE 0 END) as leaves,
    COUNT(DISTINCT display_name) as unique_people
FROM gamelog_join_leave
WHERE DATE(created_at) = DATE('now')
GROUP BY CAST(strftime('%H', created_at) AS INTEGER), location
ORDER BY hour ASC;
.output stdout

-- 17. CSV-FRIENDLY: Full Join/Leave Log
-- ============================================================================
.mode csv
.output join_leave_log.csv
SELECT 
    DATETIME(created_at) as timestamp,
    type,
    display_name,
    user_id,
    location,
    world_name
FROM gamelog_join_leave
WHERE DATE(created_at) = DATE('now')
ORDER BY created_at ASC;
.output stdout

-- ============================================================================
-- USEFUL REFERENCE QUERIES
-- ============================================================================

-- List all tables in database
-- ============================================================================
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;

-- Show table structure
-- ============================================================================
-- Replace 'gamelog_location' with table name you want to inspect
PRAGMA table_info(gamelog_location);

-- Count records in each table
-- ============================================================================
SELECT 
    'cache_avatar' as table_name, 
    (SELECT COUNT(*) FROM cache_avatar) as count
UNION ALL SELECT 'cache_world', (SELECT COUNT(*) FROM cache_world)
UNION ALL SELECT 'gamelog_event', (SELECT COUNT(*) FROM gamelog_event)
UNION ALL SELECT 'gamelog_external', (SELECT COUNT(*) FROM gamelog_external)
UNION ALL SELECT 'gamelog_join_leave', (SELECT COUNT(*) FROM gamelog_join_leave)
UNION ALL SELECT 'gamelog_location', (SELECT COUNT(*) FROM gamelog_location)
UNION ALL SELECT 'gamelog_portal_spawn', (SELECT COUNT(*) FROM gamelog_portal_spawn)
UNION ALL SELECT 'gamelog_resource_load', (SELECT COUNT(*) FROM gamelog_resource_load)
UNION ALL SELECT 'gamelog_video_play', (SELECT COUNT(*) FROM gamelog_video_play)
ORDER BY table_name;

-- Database size and performance info
-- ============================================================================
PRAGMA database_list;
PRAGMA journal_mode;
PRAGMA cache_size;
